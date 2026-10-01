// SPDX-License-Identifier: Apache-2.0
// Original API adapter. CodeWalker is a separately obtained local dependency;
// its source/binaries are not distributed or relicensed by this project.
using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;
using System.Xml;
using CodeWalker.GameFiles;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;
if (args.Length != 3 || (args[0] != "convert" && args[0] != "pack" && args[0] != "prepare-dlclist" && args[0] != "inspect-ydr"))
{
    Console.Error.WriteLine("Usage: CodeWalkerBridge convert INPUT.ydr.xml|INPUT.ycd.xml|INPUT.ytyp.xml NEW_OUTPUT, or pack SOURCE_DIRECTORY NEW_RPF");
    return 2;
}
try
{
    string source = Path.GetFullPath(args[1]);
    string destination = Path.GetFullPath(args[2]);
    if (File.Exists(destination)) throw new IOException("Refusing to overwrite an existing asset");
    if (args[0] == "inspect-ydr")
    {
        var drawable = new YdrFile();
        drawable.Load(File.ReadAllBytes(source));
        var textures = drawable.Drawable?.ShaderGroup?.TextureDictionary?.Textures?.data_items ?? [];
        var report = new { textures = textures.Select(t => new { name = t.Name, format = (uint)t.Format,
            known_format = Enum.IsDefined(typeof(TextureFormat), t.Format), width = t.Width, height = t.Height,
            mips = t.Levels, data_bytes = t.Data?.FullData?.Length ?? 0 }).ToArray(), gta_runtime_verified = false };
        File.WriteAllText(destination, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + "\n");
        Console.WriteLine(JsonSerializer.Serialize(new { textures = textures.Length,
            invalid_formats = textures.Count(t => !Enum.IsDefined(typeof(TextureFormat), t.Format)) }));
        return 0;
    }
    if (args[0] == "prepare-dlclist")
    {
        // Asset archive decoding only. Never run or patch the game executable,
        // persist key material, or read account/authentication stores.
        GTA5Keys.GenerateV2(File.ReadAllBytes(Path.Combine(source,"GTA5.exe")), null);
        if (GTA5Keys.PC_AES_KEY == null) throw new InvalidDataException("Could not identify this game's archive format key");
        GTA5Keys.LoadFromPath("", false, Convert.ToBase64String(GTA5Keys.PC_AES_KEY));
        var archive = new RpfFile(Path.Combine(source,"update","update.rpf"), "update\\update.rpf");
        var errors = new List<string>();
        archive.ScanStructure(_ => { }, message => errors.Add(message));
        if (errors.Count != 0) throw new InvalidDataException(string.Join("; ",errors));
        var entry = archive.AllEntries.OfType<RpfFileEntry>().Single(e =>
            e.Path.Replace('\\','/').EndsWith("/common/data/dlclist.xml",StringComparison.OrdinalIgnoreCase));
        var dlcListBytes = archive.ExtractFile(entry);
        var document = new XmlDocument { XmlResolver = null };
        using (var input = new MemoryStream(dlcListBytes))
        using (var reader = XmlReader.Create(input,new XmlReaderSettings { DtdProcessing=DtdProcessing.Prohibit })) document.Load(reader);
        var paths = document.SelectSingleNode("/SMandatoryPacksData/Paths") ?? throw new InvalidDataException("Unknown DLC list schema");
        const string addon = "dlcpacks:/ergt/";
        if (!paths.ChildNodes.OfType<XmlElement>().Any(e => e.InnerText.Trim().Equals(addon,StringComparison.OrdinalIgnoreCase)))
        {
            var item=document.CreateElement("Item"); item.InnerText=addon; paths.AppendChild(item);
        }
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        using (var output=new FileStream(destination,FileMode.CreateNew,FileAccess.Write))
        using (var writer=XmlWriter.Create(output,new XmlWriterSettings { Indent=true, Encoding=new System.Text.UTF8Encoding(false) })) document.Save(writer);
        Console.WriteLine("Prepared local DLC-list overlay; original game archives unchanged; no keys persisted.");
        return 0;
    }
    if (args[0] == "pack")
    {
        if (!Directory.Exists(source)) throw new DirectoryNotFoundException(source);
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        string temporary = Path.Combine(Path.GetDirectoryName(destination)!, ".ergt-pack-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(temporary);
        string oldDirectory = Directory.GetCurrentDirectory();
        byte[] archiveBytes;
        int count = 0;
        try
        {
            Directory.SetCurrentDirectory(temporary);
            // CodeWalker's root creation API uses Windows separators. Keeping
            // its temporary name relative works on macOS; copy out only after
            // all library operations and structural checks have completed.
            var archive = RpfFile.CreateNew(".", "package.rpf", RpfEncryption.OPEN);
            void AddDirectory(string folder, RpfDirectoryEntry target)
            {
                foreach (string child in Directory.EnumerateFileSystemEntries(folder).Order())
                {
                    if ((File.GetAttributes(child) & FileAttributes.ReparsePoint) != 0)
                        throw new IOException("Refusing symlink/reparse point in archive input");
                    if (Directory.Exists(child)) AddDirectory(child, RpfFile.CreateDirectory(target, Path.GetFileName(child)));
                    else { RpfFile.CreateFile(target, Path.GetFileName(child), File.ReadAllBytes(child), false); count++; }
                }
            }
            AddDirectory(source, archive.Root);
            var errors = new List<string>();
            var check = new RpfFile(archive.FilePath, "package.rpf");
            check.ScanStructure(_ => { }, message => errors.Add(message));
            if (errors.Count != 0 || check.Root == null) throw new InvalidDataException(string.Join("; ", errors));
            archiveBytes = File.ReadAllBytes(archive.FilePath);
        }
        finally { Directory.SetCurrentDirectory(oldDirectory); Directory.Delete(temporary, true); }
        using (var output = new FileStream(destination, FileMode.CreateNew, FileAccess.Write)) output.Write(archiveBytes);
        Console.WriteLine(JsonSerializer.Serialize(new { archive_structure_verified = true, gta_runtime_verified = false,
            files = count, bytes = archiveBytes.Length, sha256 = Convert.ToHexString(SHA256.HashData(archiveBytes)).ToLowerInvariant() }));
        return 0;
    }
    var xml = new XmlDocument { XmlResolver = null };
    using (var reader = XmlReader.Create(source, new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit }))
        xml.Load(reader);
    byte[] data;
    object details;
    if (source.EndsWith(".ydr.xml", StringComparison.OrdinalIgnoreCase))
    {
        string textures = source[..^".ydr.xml".Length];
        var original = XmlYdr.GetYdr(xml, textures);
        ValidateTextures(original);
        data = original.Save();
        var loaded = new YdrFile();
        loaded.Load(data);
        if (loaded.Drawable?.Skeleton?.BonesCount != original.Drawable?.Skeleton?.BonesCount)
            throw new InvalidDataException("Skeleton count changed during binary round-trip");
        ValidateTextures(loaded);
        details = new { bones = loaded.Drawable?.Skeleton?.BonesCount, drawable_present = loaded.Drawable != null,
                        collision_present = loaded.Drawable?.Bound != null,
                        textures = loaded.Drawable?.ShaderGroup?.TextureDictionary?.Textures?.data_items?.Length ?? 0,
                        texture_formats_verified = true };
    }
    else if (source.EndsWith(".ycd.xml", StringComparison.OrdinalIgnoreCase))
    {
        var original = XmlYcd.GetYcd(xml);
        data = original.Save();
        var loaded = new YcdFile();
        RpfFile.LoadResourceFile(loaded, data, 46);
        if (loaded.ClipMap.Count == 0 || loaded.AnimMap.Count == 0)
            throw new InvalidDataException("Binary animation dictionary is empty");
        details = new { clips = loaded.ClipMap.Count, animations = loaded.AnimMap.Count };
    }
    else if (source.EndsWith(".ytyp.xml", StringComparison.OrdinalIgnoreCase))
    {
        data = XmlMeta.GetData(xml, MetaFormat.RSC, source);
        var loaded = new YtypFile();
        RpfFile.LoadResourceFile(loaded, data, 2);
        if (loaded.AllArchetypes == null || loaded.AllArchetypes.Length == 0)
            throw new InvalidDataException("Archetype dictionary is empty");
        var inputs = xml.SelectNodes("/CMapTypes/archetypes/Item")!.OfType<XmlElement>().ToArray();
        if (inputs.Length != loaded.AllArchetypes.Length) throw new InvalidDataException("Archetype count changed");
        var bindings = inputs.Select(input =>
        {
            string name = input["name"]!.InnerText;
            uint nameHash = JenkHash.GenHash(name);
            var def = loaded.AllArchetypes.Single(a => a.Hash == nameHash)._BaseArchetypeDef;
            uint flags = uint.Parse(input["flags"]!.GetAttribute("value"));
            string physics = input["physicsDictionary"]?.InnerText ?? "";
            string clips = input["clipDictionary"]?.InnerText ?? "";
            string textures = input["textureDictionary"]?.InnerText ?? "";
            if (def.flags != flags || (uint)def.physicsDictionary != (physics.Length == 0 ? 0 : JenkHash.GenHash(physics)) ||
                (uint)def.clipDictionary != (clips.Length == 0 ? 0 : JenkHash.GenHash(clips)) ||
                (uint)def.textureDictionary != (textures.Length == 0 ? 0 : JenkHash.GenHash(textures)))
                throw new InvalidDataException("Archetype bindings changed during round-trip: " + name);
            return new { model = name, flags = def.flags, physics_dictionary = physics, clip_dictionary = clips, texture_dictionary = textures };
        }).ToArray();
        details = new { archetypes = loaded.AllArchetypes.Length, bindings };
    }
    else throw new ArgumentException("Unsupported input asset extension");
    Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
    using (var output = new FileStream(destination, FileMode.CreateNew, FileAccess.Write))
        output.Write(data);
    var receipt = new { format_roundtrip_verified = true, gta_runtime_verified = false,
                        bytes = data.Length, sha256 = Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant(), details };
    File.WriteAllText(destination + ".json", JsonSerializer.Serialize(receipt, new JsonSerializerOptions { WriteIndented = true }) + "\n");
    Console.WriteLine(JsonSerializer.Serialize(receipt));
    return 0;
}
catch (Exception error)
{
    Console.Error.WriteLine(error.ToString());
    return 1;
}

static void ValidateTextures(YdrFile file)
{
    var textures = file.Drawable?.ShaderGroup?.TextureDictionary?.Textures?.data_items ?? [];
    if (textures.Length == 0) throw new InvalidDataException("Creature drawable has no embedded textures");
    foreach (var texture in textures)
    {
        // CodeWalker's DXGI mapper returns enum zero for sRGB DDS variants.
        // A successful resource round-trip alone does not catch that invalid format.
        if (!Enum.IsDefined(typeof(TextureFormat), texture.Format))
            throw new InvalidDataException($"Unsupported GTA texture format {(uint)texture.Format}: {texture.Name}. Normalize the DDS before converting.");
        if (texture.Width == 0 || texture.Height == 0 || texture.Levels == 0 || texture.Stride == 0 ||
            texture.Data?.FullData == null || texture.Data.FullData.Length < texture.Stride * texture.Height)
            throw new InvalidDataException("Empty/truncated texture: " + texture.Name);
    }
}
