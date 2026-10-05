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
if (args.Length != 3 || (args[0] != "convert" && args[0] != "pack" && args[0] != "prepare-dlclist" && args[0] != "inspect-ydr" && args[0] != "inspect-ytyp"))
{
    Console.Error.WriteLine("Usage: CodeWalkerBridge convert INPUT.ydr.xml|INPUT.ycd.xml|INPUT.ytyp.xml NEW_OUTPUT, or pack SOURCE_DIRECTORY NEW_RPF");
    return 2;
}
try
{
    string source = Path.GetFullPath(args[1]);
    string destination = Path.GetFullPath(args[2]);
    if (File.Exists(destination)) throw new IOException("Refusing to overwrite an existing asset");
    if (args[0] == "inspect-ytyp")
    {
        var file = new YtypFile(); RpfFile.LoadResourceFile(file, File.ReadAllBytes(source), 2);
        var report = file.AllArchetypes.Select(a => new { name_hash = (uint)a.Hash,
            asset_name = (uint)a.BaseArchetypeDef.assetName, asset_type = a.BaseArchetypeDef.assetType.ToString(),
            flags = a.BaseArchetypeDef.flags, special = a.BaseArchetypeDef.specialAttribute }).ToArray();
        File.WriteAllText(destination,JsonSerializer.Serialize(report,new JsonSerializerOptions { WriteIndented=true }));
        Console.WriteLine(JsonSerializer.Serialize(report)); return 0;
    }
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
        int resourceCount = 0;
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
            resourceCount = ValidateResourceEntries(check);
            archiveBytes = File.ReadAllBytes(archive.FilePath);
        }
        finally { Directory.SetCurrentDirectory(oldDirectory); Directory.Delete(temporary, true); }
        using (var output = new FileStream(destination, FileMode.CreateNew, FileAccess.Write)) output.Write(archiveBytes);
        Console.WriteLine(JsonSerializer.Serialize(new { archive_structure_verified = true, gta_runtime_verified = false,
            files = count, resource_entries_verified = resourceCount, bytes = archiveBytes.Length,
            sha256 = Convert.ToHexString(SHA256.HashData(archiveBytes)).ToLowerInvariant() }));
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
        bool external = (original.Drawable?.ShaderGroup?.TextureDictionary?.Textures?.data_items?.Length ?? 0)==0;
        if (external)
        {
            string listPath=source[..^".ydr.xml".Length]+".textures.json";
            string[] dictionaries=File.Exists(listPath) ? JsonSerializer.Deserialize<string[]>(File.ReadAllText(listPath))! : [Path.GetFileName(source[..^".ydr.xml".Length]+".ytd.xml")];
            var names=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach(string relative in dictionaries)
            {
                if(Path.GetFileName(relative)!=relative || !relative.EndsWith(".ytd.xml"))throw new InvalidDataException("Unsafe texture manifest path");
                string txdPath=Path.Combine(Path.GetDirectoryName(source)!,relative);
                var txdXml=new XmlDocument { XmlResolver=null };txdXml.Load(txdPath);
                var txd=XmlYtd.GetYtd(txdXml,txdPath[..^".ytd.xml".Length]);
                ValidateTextureArray(txd.TextureDict?.Textures?.data_items ?? []);
                foreach(var t in txd.TextureDict!.Textures.data_items)
                    if(!names.Add(t.Name))throw new InvalidDataException("Duplicate parent texture: "+t.Name);
            }
            foreach(XmlNode sampler in xml.SelectNodes("/Drawable/ShaderGroup/Shaders/Item/Parameters/Item[@type='Texture']/Name")!)
                if(!names.Contains(sampler.InnerText))throw new InvalidDataException("External sampler missing: "+sampler.InnerText);
        }
        else ValidateTextures(original);
        data = original.Save();
        var loaded = new YdrFile();
        loaded.Load(data);
        if (loaded.Drawable?.Skeleton?.BonesCount != original.Drawable?.Skeleton?.BonesCount)
            throw new InvalidDataException("Skeleton count changed during binary round-trip");
        if(!external)ValidateTextures(loaded);
        details = new { bones = loaded.Drawable?.Skeleton?.BonesCount, drawable_present = loaded.Drawable != null,
                        collision_present = loaded.Drawable?.Bound != null,
                        textures = loaded.Drawable?.ShaderGroup?.TextureDictionary?.Textures?.data_items?.Length ?? 0,
                        texture_formats_verified = true, external_texture_dictionary = external };
    }
    else if (source.EndsWith(".ytd.xml", StringComparison.OrdinalIgnoreCase))
    {
        var original = XmlYtd.GetYtd(xml,source[..^".ytd.xml".Length]);
        ValidateTextureArray(original.TextureDict?.Textures?.data_items ?? []);
        data = original.Save();
        var loaded = new YtdFile();RpfFile.LoadResourceFile(loaded,data,13);
        ValidateTextureArray(loaded.TextureDict?.Textures?.data_items ?? []);
        if (loaded.TextureDict?.Textures?.data_items?.Length != original.TextureDict?.Textures?.data_items?.Length)
            throw new InvalidDataException("Texture dictionary changed during round-trip");
        // Pinned CodeWalker's Legacy reader divides mip byte counts by four,
        // truncating block-compressed 2x2/1x1 tails and rectangular mip chains.
        // Verify the full payload at its decoded native pointer instead.
        int systemBytes=RpfResourceFileEntry.GetSizeFromFlags(BitConverter.ToUInt32(data,8));
        int graphicsBytes=RpfResourceFileEntry.GetSizeFromFlags(BitConverter.ToUInt32(data,12));
        using var compressed=new MemoryStream(data,16,data.Length-16);
        using var inflater=new System.IO.Compression.DeflateStream(compressed,System.IO.Compression.CompressionMode.Decompress);
        using var expanded=new MemoryStream();inflater.CopyTo(expanded);
        if(expanded.Length!=systemBytes+graphicsBytes)throw new InvalidDataException("Resource page sizes disagree");
        var rawReader=new ResourceDataReader(systemBytes,graphicsBytes,expanded.ToArray());
        foreach(var before in original.TextureDict!.Textures.data_items)
        {
            var matches=loaded.TextureDict!.Textures.data_items.Where(t=>t.Name==before.Name).ToArray();
            if(matches.Length!=1)throw new InvalidDataException("Texture name roundtrip: "+before.Name+" available "+string.Join(",",loaded.TextureDict.Textures.data_items.Select(t=>t.Name)));
            var after=matches[0];
            rawReader.Position=(long)after.DataPointer;
            var recovered=rawReader.ReadBytes(before.Data.FullData.Length);
            if(before.Format!=after.Format || before.Width!=after.Width || before.Height!=after.Height || before.Levels!=after.Levels || !before.Data.FullData.SequenceEqual(recovered))
                throw new InvalidDataException("Texture pixels/mips changed in native round-trip: "+before.Name+" bytes "+before.Data.FullData.Length+"->"+after.Data.FullData.Length+" format "+before.Format+"->"+after.Format+" dimensions "+before.Width+"x"+before.Height+"->"+after.Width+"x"+after.Height+" levels "+before.Levels+"->"+after.Levels);
        }
        details = new { textures = loaded.TextureDict?.Textures?.data_items?.Length, external_texture_dictionary = true, pixel_payloads_verified = true };
    }
    else if (source.EndsWith(".ycd.xml", StringComparison.OrdinalIgnoreCase))
    {
        var original = XmlYcd.GetYcd(xml);
        data = original.Save();
        var loaded = new YcdFile();
        RpfFile.LoadResourceFile(loaded, data, 46);
        if (loaded.ClipMap.Count == 0 || loaded.AnimMap.Count == 0)
            throw new InvalidDataException("Binary animation dictionary is empty");
        // Validate decoded native samples, including last frames and compact
        // quaternions. Bone/clip counts alone previously hid a broken pose.
        if (loaded.AnimMap.Count != original.AnimMap.Count || loaded.ClipMap.Count != original.ClipMap.Count)
            throw new InvalidDataException("Animation/clip count changed");
        int checkedSamples = 0; float maxError = 0;
        foreach (var pair in original.AnimMap)
        {
            var expected = pair.Value.Animation;
            if (!loaded.AnimMap.TryGetValue(pair.Key, out var entry)) throw new InvalidDataException("Missing animation");
            var actual = entry.Animation;
            if (actual.Frames != expected.Frames || Math.Abs(actual.Duration - expected.Duration) > 1e-5f ||
                actual.BoneIds.data_items.Length != expected.BoneIds.data_items.Length)
                throw new InvalidDataException("Animation timing/layout changed");
            for (int frame = 0; frame < expected.Frames; frame++)
            for (int bone = 0; bone < expected.BoneIds.data_items.Length; bone++)
            {
                var id = expected.BoneIds.data_items[bone]; var readId = actual.BoneIds.data_items[bone];
                if (id.BoneId != readId.BoneId || id.Track != readId.Track) throw new InvalidDataException("Bone mapping changed");
                var a = expected.Sequences.data_items[frame / expected.SequenceFrameLimit].Sequences[bone].EvaluateVector(frame % expected.SequenceFrameLimit);
                var b = actual.Sequences.data_items[frame / actual.SequenceFrameLimit].Sequences[bone].EvaluateVector(frame % actual.SequenceFrameLimit);
                var error = Math.Max(Math.Max(Math.Abs(a.X-b.X),Math.Abs(a.Y-b.Y)),Math.Max(Math.Abs(a.Z-b.Z),Math.Abs(a.W-b.W)));
                if (!float.IsFinite(error) || error > 2e-5f) throw new InvalidDataException("Native animation sample changed");
                maxError = Math.Max(maxError,error); checkedSamples++;
            }
        }
        details = new { clips = loaded.ClipMap.Count, animations = loaded.AnimMap.Count,
            checked_native_samples = checkedSamples, max_component_error = maxError };
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
    ValidateTextureArray(textures);
}

static void ValidateTextureArray(Texture[] textures)
{
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

static int ValidateResourceEntries(RpfFile archive)
{
    int count = 0;
    foreach (var entry in archive.AllEntries.OfType<RpfFileEntry>())
    {
        int expected = Path.GetExtension(entry.Name).ToLowerInvariant() switch
        {
            ".ydr" => 165, ".ycd" => 46, ".ytyp" => 2, ".ytd" => 13, _ => 0
        };
        if (expected == 0) continue;
        if (entry is not RpfResourceFileEntry resource || resource.Version != expected)
            throw new InvalidDataException("Wrong native resource entry type/version: " + entry.Name);
        count++;
    }
    foreach (var child in archive.Children ?? []) count += ValidateResourceEntries(child);
    return count;
}
