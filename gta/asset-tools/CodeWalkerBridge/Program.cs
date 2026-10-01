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
if (args.Length != 3 || args[0] != "convert")
{
    Console.Error.WriteLine("Usage: CodeWalkerBridge convert INPUT.ydr.xml|INPUT.ycd.xml NEW_OUTPUT");
    return 2;
}
try
{
    string source = Path.GetFullPath(args[1]);
    string destination = Path.GetFullPath(args[2]);
    if (File.Exists(destination)) throw new IOException("Refusing to overwrite an existing asset");
    var xml = new XmlDocument { XmlResolver = null };
    using (var reader = XmlReader.Create(source, new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit }))
        xml.Load(reader);
    byte[] data;
    object details;
    if (source.EndsWith(".ydr.xml", StringComparison.OrdinalIgnoreCase))
    {
        string textures = source[..^".ydr.xml".Length];
        var original = XmlYdr.GetYdr(xml, textures);
        data = original.Save();
        var loaded = new YdrFile();
        loaded.Load(data);
        if (loaded.Drawable?.Skeleton?.BonesCount != original.Drawable?.Skeleton?.BonesCount)
            throw new InvalidDataException("Skeleton count changed during binary round-trip");
        details = new { bones = loaded.Drawable?.Skeleton?.BonesCount, drawable_present = loaded.Drawable != null };
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
