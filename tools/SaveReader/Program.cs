using System.Text.Json;
using PKHeX.Core;

// This executable only reads the temporary snapshot supplied by the launcher.
var options = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };
try
{
    if (args.Length != 1) throw new ArgumentException("Indica un archivo de partida.");
    var save = SaveUtil.GetSaveFile(args[0]) ?? throw new InvalidDataException("Formato de partida no reconocido. Usa un guardado normal, no un save state.");
    if (!save.ChecksumsValid) throw new InvalidDataException("La partida no supera la comprobación de integridad de PKHeX.Core.");
    if (save.Generation is < 1 or > 7) throw new InvalidDataException("Esta etapa admite los juegos del catálogo de las generaciones I a VII.");
    var strings = GameInfo.GetStrings("es");
    string Label(string[] values, int id) => id >= 0 && id < values.Length ? values[id] : $"#{id}";
    object Pokemon(PKM p, int slot) => new {
        slot, species = p.Species, speciesName = Label(strings.specieslist, p.Species),
        nickname = p.Nickname, level = p.CurrentLevel, form = p.Form, isEgg = p.IsEgg,
        shiny = p.Format >= 2 ? (bool?)p.IsShiny : null,
        heldItem = p.Format >= 2 ? Label(strings.GetItemStrings(p.Context), p.HeldItem) : null,
        moves = new[] { p.Move1, p.Move2, p.Move3, p.Move4 }.Where(m => m != 0).Select(m => Label(strings.movelist, m)).ToArray(),
    };
    var party = save.PartyData.Select((p, i) => (p, i)).Where(x => x.p.Species != 0).Select(x => Pokemon(x.p, x.i + 1)).ToArray();
    // BoxCount is the format's limit, not necessarily what this save has unlocked.
    var unlocked = save is SAV6XY or SAV6AO && save.BoxesUnlocked > 0
        ? Math.Min(save.BoxesUnlocked, save.BoxCount) : save.BoxCount;
    var boxes = Enumerable.Range(0, save.BoxCount).Select(b => new {
        number = b + 1, capacity = save.BoxSlotCount, unlocked = b < unlocked,
        name = save is IBoxDetailNameRead names ? names.GetBoxName(b) : $"Caja {b + 1}",
        pokemon = Enumerable.Range(0, save.BoxSlotCount).Select(s => (p: save.GetBoxSlotAtIndex(b, s), s))
            .Where(x => x.p.Species != 0).Select(x => Pokemon(x.p, x.s + 1)).ToArray(),
    }).Where(box => box.unlocked || box.pokemon.Length != 0).ToArray();
    // Generation VI stores six independent Pokémon in its Battle Box.
    BattleBox6? battle = save switch {
        SAV6XY xy => xy.BattleBox,
        SAV6AO ao => ao.BattleBox,
        _ => null,
    };
    var battleBox = battle is null ? null : new {
        capacity = BattleBox6.Count, locked = battle.Locked,
        pokemon = Enumerable.Range(0, BattleBox6.Count)
            .Select(i => (p: save.GetStoredSlot(battle.GetSlot(i).Span), i))
            .Where(x => x.p.Species != 0).Select(x => Pokemon(x.p, x.i + 1)).ToArray(),
    };
    var seen = new List<int>();
    var caught = new List<int>();
    if (save.HasPokeDex)
        for (ushort species = 1; species <= save.MaxSpeciesID; species++) {
            if (save.GetSeen(species)) seen.Add(species);
            if (save.GetCaught(species)) caught.Add(species);
        }
    Console.WriteLine(JsonSerializer.Serialize(new {
        schemaVersion = 1, coreVersion = typeof(SaveFile).Assembly.GetName().Version?.ToString(), version = save.Version.ToString(), generation = save.Generation,
        trainer = new { name = save.OT, id = save.TID16, playTime = save.PlayTimeString },
        party, boxes, battleBox, storage = new { unlockedBoxes = unlocked, maxBoxes = save.BoxCount }, dex = new { available = save.HasPokeDex, seen, caught },
    }, options));
}
catch (Exception error)
{
    Console.WriteLine(JsonSerializer.Serialize(new { schemaVersion = 1, error = error.Message }, options));
    Environment.ExitCode = 1;
}
