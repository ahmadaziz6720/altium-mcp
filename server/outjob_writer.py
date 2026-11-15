"""Write an Altium .OutJob from a preset, or edit the outputs of one (A12).

Kept free of Altium and Windows imports, like outjob_parser, which reads the
file back. An OutJob is an INI file: [OutputGroup1] lists the containers
(OutputMedium<m>) and the outputs (OutputType<n>), each output's settings in
Configuration<n>_Item<k> records ("Key=Value|Key=Value"), and which
containers it goes to (OutputEnabled<n>_OutputMedium<m>, the output's place
in that container, 0 for none); [PublishSettings] and
[GeneratedFilesSettings] hold each container's folder and options.

The records written are those of Altium's own example OutJobs (the
Bluetooth Sentinel and Mini PC examples of AD25), with the settings asked put
in. What each setting is called in the file was probed in AD25 on
2026-11-15: an OutJob written so, run by run_output_jobs, wrote the files
with the units, format, zeroes and layers asked.
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple

PRESET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output_presets")

# Altium's V7 layer IDs (outjob_parser.layer_name is the other way)
_LAYER_IDS = {
    "top layer": 0x01000001, "bottom layer": 0x0100FFFF,
    "top overlay": 0x01030006, "bottom overlay": 0x01030007,
    "top paste": 0x01030008, "bottom paste": 0x01030009,
    "top solder": 0x0103000A, "bottom solder": 0x0103000B,
    "keep-out layer": 0x0103000D,
    "top pad master": 0x01030018, "bottom pad master": 0x01030019,
}
MID_LAYERS = 30
PLANES = 16
MECHANICAL = 32

# Every copper layer Altium has: it plots only those in the board's stack
COPPER = (["Top Layer"] + [f"Mid Layer {i}" for i in range(1, MID_LAYERS + 1)]
          + [f"Internal Plane {i}" for i in range(1, PLANES + 1)] + ["Bottom Layer"])

UNITS = {"mm": "Metric", "inch": "Imperial"}
# Altium's formats per unit, integer and decimal digits
GERBER_FORMATS = {"mm": ("4:2", "4:3", "4:4"), "inch": ("2:3", "2:4", "2:5")}
DRILL_FORMATS = {"mm": ("4:2", "4:3", "4:4"), "inch": ("2:3", "2:4", "2:5")}
ZEROES = {"suppress_leading": "SuppressLeadingZeroes", "suppress_trailing": "SuppressTrailingZeroes",
          "keep": "KeepLeadingAndTrailingZeroes"}
ORIGINS = {"absolute": "Absolute", "relative": "Relative"}
PNP_UNITS = {"mm": "Metric", "mil": "Imperial"}
PNP_FORMATS = ("csv", "txt")
# BatchMode per file format (2 also writes .xlsx; 7 and up are refused by Altium)
BOM_FORMATS = {"csv": "0", "txt": "1", "html": "3", "xml": "4", "xlsx": "5", "pdf": "6"}

# What each setting group is in the file
KINDS = {
    "gerber": {"type": "Gerber", "name": "Gerber Files", "category": "Fabrication", "record": "GerberView"},
    "nc_drill": {"type": "NC Drill", "name": "NC Drill Files", "category": "Fabrication", "record": "DrillView"},
    "bom": {"type": "BOM_PartType", "name": "Bill of Materials", "category": "Report", "record": None},
    "pick_place": {"type": "Pick Place", "name": "Pick Place", "category": "Assembly", "record": "PickPlaceView"},
}
SETTING_KEYS = {
    "gerber": ("units", "format", "zeroes", "origin", "layers", "board_profile"),
    "nc_drill": ("units", "format", "zeroes", "origin", "separate_plated"),
    "bom": ("format", "columns", "group_by"),
    "pick_place": ("units", "formats"),
}

# Altium's own records (Bluetooth Sentinel's Fabrication.OutJob, AD25), the
# settings asked written over them
GERBER_BASE = (
    "AddToAllLayerClasses.Set= |AddToAllPlots.Set=SerializeLayerHash.Version~2,ClassName~TLayerToBoolean|"
    "CentrePlots=False|DrillDrawingSymbol=GraphicsSymbol|DrillDrawingSymbolSize=500000|EmbeddedApertures=True|"
    "FilmBorderSize=10000000|FilmXSize=200000000|FilmYSize=160000000|FlashAllFills=False|FlashPadShapes=True|"
    "G54OnApertureChange=False|GenerateDRCRulesFile=False|GenerateReliefShapes=True|GerberUnit=Imperial|"
    "IncludeUnconnectedMidLayerPads=False|LayerClassesMirror.Set= |LayerClassesPlot.Set= |"
    "LeadingAndTrailingZeroesMode=SuppressLeadingZeroes|MaxApertureSize=2500000|MinusApertureTolerance=50|"
    "Mirror.Set=SerializeLayerHash.Version~2,ClassName~TLayerToBoolean|MirrorDrillDrawingPlots=False|"
    "MirrorDrillGuidePlots=False|NumberOfDecimals=5|OptimizeChangeLocationCommands=True|OriginPosition=Relative|"
    "Panelize=False|Plot.Set=SerializeLayerHash.Version~2,ClassName~TLayerToBoolean|PlotBoardProfile=False|"
    "PlotPositivePlaneLayers=False|PlotUsedDrillDrawingLayerPairs=False|PlotUsedDrillGuideLayerPairs=False|"
    "PlusApertureTolerance=50|Record=GerberView|SoftwareArcs=False|Sorted=False")
DRILL_BASE = (
    "BoardEdgeRoutToolDia=2000000|GenerateBoardEdgeRout=False|GenerateDrilledSlotsG85=False|"
    "GenerateEIADrillFile=False|GenerateSeparatePlatedNonPlatedFiles=False|NumberOfDecimals=5|NumberOfUnits=2|"
    "OptimizeChangeLocationCommands=True|OriginPosition=Relative|Record=DrillView|Units=Imperial|"
    "ZeroesMode=SuppressTrailingZeroes")
PNP_BASE = "Record=PickPlaceView|Units=Imperial|GenerateCSVFormat=False|GenerateTextFormat=True"
# OpenExported and ShowExportOptions off: a run opens no spreadsheet and no dialog
BOM_GENERAL_BASE = (
    "OpenExported=False|AddToProject=False|ForceFit=False|NotFitted=False|Database=False|IncludePCBData=False|"
    "ShowExportOptions=False|TemplateFilename=|BatchMode=0|FormWidth=1185|FormHeight=665|SupplierProdQty=1|"
    "SupplierAutoQty=False|SupplierUseCachedPricing=False|SupplierCurrency=<none>")


class OutJobError(ValueError):
    """A request that cannot be written; nothing was changed."""


# --- Layers ---------------------------------------------------------------

def layer_id(name: str) -> int:
    """Altium's V7 layer ID of a layer name as outjob_parser.layer_name gives it."""
    key = " ".join(str(name).split()).lower()
    if key in _LAYER_IDS:
        return _LAYER_IDS[key]
    m = re.fullmatch(r"(mid layer|internal plane|mechanical)\s*(\d+)", key)
    if m:
        kind, n = m.group(1), int(m.group(2))
        top = {"mid layer": MID_LAYERS, "internal plane": PLANES, "mechanical": MECHANICAL}[kind]
        if 1 <= n <= top:
            return {"mid layer": 0x01000001, "internal plane": 0x01010000, "mechanical": 0x01020000}[kind] + n
    raise OutJobError(f"unknown layer '{name}': one of Top Layer, Mid Layer 1-{MID_LAYERS}, Internal Plane "
                      f"1-{PLANES}, Bottom Layer, Top/Bottom Overlay, Top/Bottom Solder, Top/Bottom Paste, "
                      f"Mechanical 1-{MECHANICAL}, Keep-Out Layer, or 'copper' for every copper layer")


def layer_ids(names) -> List[int]:
    """The IDs of a layer list, 'copper' standing for every copper layer;
    each once, in order."""
    if isinstance(names, str) or not isinstance(names, (list, tuple)) or not names:
        raise OutJobError("gerber layers: a non-empty list of layer names")
    out = []
    for name in names:
        expanded = COPPER if str(name).strip().lower() == "copper" else [name]
        for n in expanded:
            i = layer_id(n)
            if i not in out:
                out.append(i)
    return out


def layer_set_text(ids: List[int]) -> str:
    return "SerializeLayerHash.Version~2,ClassName~TLayerToBoolean" + "".join(f",{i}~1" for i in ids)


# --- Pipe records ---------------------------------------------------------

def parse_record(text: str) -> List[Tuple[str, str]]:
    """'K=V|K=V' as an ordered list of pairs (a part with no '=' is kept as a key)."""
    out = []
    for part in text.split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            out.append((k, v))
        elif part:
            out.append((part, None))
    return out


def record_text(pairs: List[Tuple[str, str]]) -> str:
    return "|".join(k if v is None else f"{k}={v}" for k, v in pairs)


def update_record(text: str, values: Dict[str, str]) -> str:
    """The record with values put in: a key it has keeps its place, a new
    one goes at the end."""
    pairs = parse_record(text)
    seen = set()
    for i, (k, _) in enumerate(pairs):
        if k in values:
            pairs[i] = (k, values[k])
            seen.add(k)
    pairs += [(k, v) for k, v in values.items() if k not in seen]
    return record_text(pairs)


def _clean(text: str, what: str) -> str:
    text = str(text)
    if any(c in text for c in "|=\r\n") or not text.strip():
        raise OutJobError(f"{what} '{text}': not empty, and no '|', '=' or line break")
    return text.strip()


# --- Settings: what is asked, checked, as the file's keys ------------------

def _choice(spec: dict, key: str, table: dict, what: str) -> Optional[str]:
    if key not in spec:
        return None
    value = str(spec[key]).strip().lower()
    if value not in table:
        raise OutJobError(f"{what} {key} '{spec[key]}': one of {', '.join(table)}")
    return table[value]


def _bool(spec: dict, key: str, what: str) -> Optional[str]:
    if key not in spec:
        return None
    if not isinstance(spec[key], bool):
        raise OutJobError(f"{what} {key}: true or false")
    return "True" if spec[key] else "False"


def _format(spec: dict, formats: dict, units_now: str, what: str) -> Optional[Tuple[str, str]]:
    """(integer digits, decimals) of spec's format, checked against its units
    (or the units the file has when spec names none)."""
    if "format" not in spec:
        return None
    unit = str(spec.get("units", units_now)).strip().lower()
    fmt = str(spec["format"]).replace(" ", "")
    if fmt not in formats.get(unit, ()):
        raise OutJobError(f"{what} format '{spec['format']}' in {unit}: one of {', '.join(formats.get(unit, ()))}")
    a, b = fmt.split(":")
    return a, b


def _check_keys(kind: str, spec) -> dict:
    if not isinstance(spec, dict):
        raise OutJobError(f"{kind}: an object of settings ({', '.join(SETTING_KEYS[kind])})")
    unknown = sorted(set(spec) - set(SETTING_KEYS[kind]))
    if unknown:
        raise OutJobError(f"{kind}: unknown setting {', '.join(unknown)}; one of {', '.join(SETTING_KEYS[kind])}")
    return spec


def gerber_values(spec: dict, current_units: str = "mm") -> Dict[str, str]:
    """The GerberView keys for a gerber spec. current_units: the unit the
    file has, for a format given without units."""
    spec = _check_keys("gerber", spec)
    out = {}
    if "units" in spec:
        out["GerberUnit"] = _choice(spec, "units", UNITS, "gerber")
    fmt = _format(spec, GERBER_FORMATS, current_units, "gerber")
    if "units" in spec and not fmt and str(spec["units"]).strip().lower() != current_units:
        raise OutJobError("gerber: a change of units needs its format too (mm 4:2-4:4, inch 2:3-2:5)")
    if fmt:
        out["NumberOfDecimals"] = fmt[1]
    if "zeroes" in spec:
        out["LeadingAndTrailingZeroesMode"] = _choice(spec, "zeroes", ZEROES, "gerber")
    if "origin" in spec:
        out["OriginPosition"] = _choice(spec, "origin", ORIGINS, "gerber")
    if "layers" in spec:
        out["Plot.Set"] = layer_set_text(layer_ids(spec["layers"]))
    if "board_profile" in spec:
        out["PlotBoardProfile"] = _bool(spec, "board_profile", "gerber")
    return out


def drill_values(spec: dict, current_units: str = "inch") -> Dict[str, str]:
    spec = _check_keys("nc_drill", spec)
    out = {}
    if "units" in spec:
        out["Units"] = _choice(spec, "units", UNITS, "nc_drill")
    fmt = _format(spec, DRILL_FORMATS, current_units, "nc_drill")
    if "units" in spec and not fmt and str(spec["units"]).strip().lower() != current_units:
        raise OutJobError("nc_drill: a change of units needs its format too (mm 4:2-4:4, inch 2:3-2:5)")
    if fmt:
        out["NumberOfUnits"], out["NumberOfDecimals"] = fmt
    if "zeroes" in spec:
        out["ZeroesMode"] = _choice(spec, "zeroes", ZEROES, "nc_drill")
    if "origin" in spec:
        out["OriginPosition"] = _choice(spec, "origin", ORIGINS, "nc_drill")
    if "separate_plated" in spec:
        out["GenerateSeparatePlatedNonPlatedFiles"] = _bool(spec, "separate_plated", "nc_drill")
    return out


def pnp_values(spec: dict) -> Dict[str, str]:
    spec = _check_keys("pick_place", spec)
    out = {}
    if "units" in spec:
        out["Units"] = _choice(spec, "units", PNP_UNITS, "pick_place")
    if "formats" in spec:
        formats = spec["formats"]
        if isinstance(formats, str):
            formats = [formats]
        formats = [str(f).strip().lower() for f in formats or []]
        if not formats or any(f not in PNP_FORMATS for f in formats):
            raise OutJobError(f"pick_place formats {spec['formats']}: a non-empty list of {', '.join(PNP_FORMATS)}")
        out["GenerateCSVFormat"] = "True" if "csv" in formats else "False"
        out["GenerateTextFormat"] = "True" if "txt" in formats else "False"
    return out


def bom_values(spec: dict) -> Dict[str, Optional[str]]:
    """The BOM's items by name: General's BatchMode, VisibleOrder and
    GroupOrder (a whole item text each)."""
    spec = _check_keys("bom", spec)
    out = {}
    if "format" in spec:
        out["BatchMode"] = _choice(spec, "format", BOM_FORMATS, "bom")
    columns = None
    if "columns" in spec:
        columns = spec["columns"]
        if isinstance(columns, str) or not isinstance(columns, (list, tuple)) or not columns:
            raise OutJobError("bom columns: a non-empty list of column names (a parameter's name for its column)")
        columns = [_clean(c, "bom column") for c in columns]
        if len({c.lower() for c in columns}) != len(columns):
            raise OutJobError("bom columns: a column named twice")
        out["VisibleOrder"] = "|".join(f"{c}=100" for c in columns)
    if "group_by" in spec:
        group = spec["group_by"]
        if isinstance(group, str) or not isinstance(group, (list, tuple)):
            raise OutJobError("bom group_by: a list of column names (empty: one row per part placed)")
        group = [_clean(c, "bom group_by column") for c in group]
        out["GroupOrder"] = "|".join(f"{c}=True" for c in group)
    return out


# --- The INI document, kept line by line -----------------------------------

class IniDoc:
    """An INI text kept as it is: lines not touched are written back as read."""

    def __init__(self, text: str):
        self.sections: List[list] = []  # [name or None, [lines]]
        current = [None, []]
        self.sections.append(current)
        for line in text.splitlines():
            m = re.fullmatch(r"\s*\[(.+)\]\s*", line)
            if m:
                current = [m.group(1), []]
                self.sections.append(current)
            else:
                current[1].append(line)

    def text(self) -> str:
        out = []
        for name, lines in self.sections:
            if name is not None:
                out.append(f"[{name}]")
            out.extend(lines)
        return "\r\n".join(out) + "\r\n"

    def section(self, name: str, create: bool = True) -> Optional[list]:
        for sec in self.sections:
            if sec[0] is not None and sec[0].lower() == name.lower():
                return sec[1]
        if not create:
            return None
        lines = self.sections[-1][1]
        if lines and lines[-1].strip():
            lines.append("")
        sec = [name, []]
        self.sections.append(sec)
        return sec[1]

    @staticmethod
    def _find(lines: list, key: str) -> int:
        for i, line in enumerate(lines):
            if "=" in line and line.split("=", 1)[0] == key:
                return i
        return -1

    def get(self, section: str, key: str, default: Optional[str] = None) -> Optional[str]:
        lines = self.section(section, create=False)
        if lines is None:
            return default
        i = self._find(lines, key)
        return lines[i].split("=", 1)[1] if i >= 0 else default

    def set(self, section: str, key: str, value: str, after: Optional[str] = None):
        """Replace key's value in place; a new key goes after the key named
        by after when there is one, else at the end of the section."""
        lines = self.section(section)
        i = self._find(lines, key)
        if i >= 0:
            lines[i] = f"{key}={value}"
            return
        j = self._find(lines, after) if after else -1
        if j < 0:
            j = len(lines) - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
        lines.insert(j + 1, f"{key}={value}")

    def numbered(self, section: str, prefix: str) -> List[Tuple[int, str]]:
        out, n = [], 1
        while True:
            v = self.get(section, f"{prefix}{n}")
            if v is None:
                return out
            out.append((n, v))
            n += 1


def read_text(path: str) -> Tuple[str, str]:
    """An OutJob's text and the encoding to write it back in: utf-8-sig only
    when it starts with the mark, utf-8 when it holds UTF-8 beyond ASCII,
    else Windows' ANSI (cp1252, then latin-1 for its five undefined bytes),
    which is what Altium writes."""
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    encodings = ("cp1252", "latin-1") if raw.isascii() else ("utf-8", "cp1252", "latin-1")
    for enc in encodings:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise OutJobError(f"{path}: not text")


# --- Presets ---------------------------------------------------------------

def load_presets(folder: str = PRESET_DIR) -> Dict[str, dict]:
    """OutJob preset name -> its settings, with the file's service and the
    pages its settings come from."""
    out = {}
    if not os.path.isdir(folder):
        return out
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(folder, fname), encoding="utf-8") as f:
            data = json.load(f)
        for name, build in data.get("outjob_presets", {}).items():
            out[name] = dict(build, service=data.get("service"), sources=data.get("sources", {}), file=fname)
    return out


def preset_specs(preset: dict) -> Dict[str, dict]:
    """A preset's settings per kind, in the writer's keys only."""
    return {kind: {k: v for k, v in preset[kind].items() if k in SETTING_KEYS[kind]}
            for kind in KINDS if kind in preset}


# --- Writing ----------------------------------------------------------------

GROUP = "OutputGroup1"
PUBLISH = "PublishSettings"
GENERATED = "GeneratedFilesSettings"


def _container_index(doc: IniDoc, name: str) -> int:
    for m, cname in doc.numbered(GROUP, "OutputMedium"):
        if cname == name:
            return m
    return 0


def _outputs(doc: IniDoc) -> List[Tuple[int, str]]:
    return doc.numbered(GROUP, "OutputType")


def _last_output_key(doc: IniDoc) -> Optional[str]:
    """The last line of the last output, for a new output to follow."""
    lines = doc.section(GROUP)
    for line in reversed(lines):
        key = line.split("=", 1)[0]
        if re.match(r"(OutputType|OutputName|OutputCategory|OutputDocumentPath|OutputVariantName|OutputEnabled|"
                    r"OutputDefault|Configuration|PageOptions)\d", key):
            return key
    return None


def add_container(doc: IniDoc, name: str) -> int:
    """A new GeneratedFiles container, connected to no output yet; its index."""
    mediums = doc.numbered(GROUP, "OutputMedium")
    m = len(mediums) + 1
    after = f"OutputMedium{m - 1}_Type" if mediums else "PrinterOptions"
    # a medium's own keys (_Type, _Printer, ...) follow it; the new one goes after them
    lines = doc.section(GROUP)
    if mediums:
        idx = max(i for i, l in enumerate(lines) if re.match(rf"OutputMedium{m - 1}(_|=)", l))
        after = lines[idx].split("=", 1)[0]
    doc.set(GROUP, f"OutputMedium{m}", name, after=after)
    doc.set(GROUP, f"OutputMedium{m}_Type", "GeneratedFiles", after=f"OutputMedium{m}")
    for n, _ in _outputs(doc):
        prev = f"OutputEnabled{n}_OutputMedium{m - 1}" if m > 1 else f"OutputEnabled{n}"
        doc.set(GROUP, f"OutputEnabled{n}_OutputMedium{m}", "0", after=prev)
    for key, value in (("OutputFilePath", ""), ("ReleaseManaged", "1"), ("OutputBasePath", ""),
                       ("OutputPathMedia", ""), ("OutputPathMediaValue", ""), ("OutputPathOutputer", ""),
                       ("OutputPathOutputerPrefix", ""), ("OutputPathOutputerValue", ""), ("OutputFileName", ""),
                       ("OutputFileNameMulti", ""), ("UseOutputNameForMulti", "1"), ("OutputFileNameSpecial", ""),
                       ("OpenOutput", "0")):
        doc.set(PUBLISH, f"{key}{m}", value)
    for key, value in (("RelativeOutputPath", ""), ("OpenOutputs", "0"), ("AddToProject", "0"),
                       ("TimestampFolder", "0"), ("UseOutputName", "0"), ("OpenODBOutput", "0"),
                       ("OpenGerberOutput", "0"), ("OpenNCDrillOutput", "0"), ("OpenIPCOutput", "0"),
                       ("EnableReload", "0")):
        doc.set(GENERATED, f"{key}{m}", value)
    return m


def set_output_folder(doc: IniDoc, m: int, folder: str):
    """Container m writes into folder (relative to the project's folder, or
    absolute), all its files there: not release managed, no subfolder per
    output type."""
    doc.set(PUBLISH, f"ReleaseManaged{m}", "0")
    doc.set(PUBLISH, f"OutputBasePath{m}", folder)
    doc.set(PUBLISH, f"OutputPathMedia{m}", "")
    doc.set(PUBLISH, f"OutputPathOutputer{m}", "")
    doc.set(GENERATED, f"RelativeOutputPath{m}", folder)


def add_output(doc: IniDoc, kind: str) -> int:
    """A new output of kind with Altium's default record, connected to no
    container yet; its index."""
    info = KINDS[kind]
    n = len(_outputs(doc)) + 1
    after = _last_output_key(doc) or f"OutputMedium{len(doc.numbered(GROUP, 'OutputMedium'))}_Type"
    keys = [(f"OutputType{n}", info["type"]), (f"OutputName{n}", info["name"]),
            (f"OutputCategory{n}", info["category"]), (f"OutputDocumentPath{n}", ""),
            (f"OutputVariantName{n}", ""), (f"OutputEnabled{n}", "1")]
    keys += [(f"OutputEnabled{n}_OutputMedium{m}", "0") for m, _ in doc.numbered(GROUP, "OutputMedium")]
    keys.append((f"OutputDefault{n}", "0"))
    if kind == "bom":
        items = [("General", BOM_GENERAL_BASE), ("GroupOrder", "Comment=True|Footprint=True"),
                 ("SortOrder", "Designator=Up|Comment=Up|Footprint=Up"),
                 ("VisibleOrder", "Comment=100|Designator=100|Footprint=100|Quantity=100")]
    else:
        base = {"gerber": GERBER_BASE, "nc_drill": DRILL_BASE, "pick_place": PNP_BASE}[kind]
        items = [("OutputConfigurationParameter1", base)]
    for k, (iname, value) in enumerate(items, 1):
        keys += [(f"Configuration{n}_Name{k}", iname), (f"Configuration{n}_Item{k}", value)]
    for key, value in keys:
        doc.set(GROUP, key, value, after=after)
        after = key
    return n


def connect(doc: IniDoc, n: int, m: int) -> bool:
    """Output n goes to container m (its place: after the container's
    others); False when it already did."""
    current = doc.get(GROUP, f"OutputEnabled{n}_OutputMedium{m}", "0")
    if current not in ("0", ""):
        return False
    places = [int(v) for k, _ in _outputs(doc)
              for v in [doc.get(GROUP, f"OutputEnabled{k}_OutputMedium{m}", "0")] if v.isdigit()]
    after = f"OutputEnabled{n}_OutputMedium{m - 1}" if m > 1 else f"OutputEnabled{n}"
    doc.set(GROUP, f"OutputEnabled{n}_OutputMedium{m}", str(max(places + [0]) + 1), after=after)
    return True


def _items(doc: IniDoc, n: int) -> List[Tuple[int, str, str]]:
    """Output n's (k, item name, item text)."""
    return [(k, doc.get(GROUP, f"Configuration{n}_Name{k}", ""), v)
            for k, v in doc.numbered(GROUP, f"Configuration{n}_Item")]


def _set_item(doc: IniDoc, n: int, name: str, text: str):
    for k, iname, _ in _items(doc, n):
        if iname == name:
            doc.set(GROUP, f"Configuration{n}_Item{k}", text)
            return
    items = _items(doc, n)
    k = len(items) + 1
    after = f"Configuration{n}_Item{k - 1}" if items else f"OutputDefault{n}"
    doc.set(GROUP, f"Configuration{n}_Name{k}", name, after=after)
    doc.set(GROUP, f"Configuration{n}_Item{k}", text, after=f"Configuration{n}_Name{k}")


def _record_item(doc: IniDoc, n: int, record: str) -> Tuple[int, str]:
    """Output n's item whose record is record, added from Altium's default
    when it has none."""
    for k, _, text in _items(doc, n):
        if dict((a, b) for a, b in parse_record(text)).get("Record") == record:
            return k, text
    base = {"GerberView": GERBER_BASE, "DrillView": DRILL_BASE, "PickPlaceView": PNP_BASE}[record]
    _set_item(doc, n, f"OutputConfigurationParameter{len(_items(doc, n)) + 1}", base)
    return len(_items(doc, n)), base


def _units_now(text: str, key: str, table: dict) -> str:
    value = dict(parse_record(text)).get(key)
    for k, v in table.items():
        if v == value:
            return k
    return list(table)[0]


def write_settings(doc: IniDoc, n: int, kind: str, spec: dict):
    """Put a kind's settings into output n's record(s)."""
    if kind == "bom":
        values = bom_values(spec)
        if "BatchMode" in values:
            general = next((t for _, iname, t in _items(doc, n) if iname == "General"), BOM_GENERAL_BASE)
            _set_item(doc, n, "General", update_record(general, {"BatchMode": values["BatchMode"],
                                                                 "OpenExported": "False",
                                                                 "ShowExportOptions": "False"}))
        for item in ("VisibleOrder", "GroupOrder"):
            if item in values:
                _set_item(doc, n, item, values[item])
        return
    record = KINDS[kind]["record"]
    k, text = _record_item(doc, n, record)
    if kind == "gerber":
        values = gerber_values(spec, _units_now(text, "GerberUnit", UNITS))
    elif kind == "nc_drill":
        values = drill_values(spec, _units_now(text, "Units", UNITS))
    else:
        values = pnp_values(spec)
    doc.set(GROUP, f"Configuration{n}_Item{k}", update_record(text, values))


def new_document(container: str) -> IniDoc:
    """An OutJob with no output and one GeneratedFiles container, as Altium
    begins one."""
    head = ["[OutputJobFile]", "Version=1.0", "Caption=", "Description=", "VaultGUID=", "ItemGUID=", "ItemHRID=",
            "RevisionGUID=", "RevisionId=", "VaultHRID=", "AutoItemHRID=", "NextRevId=", "FolderGUID=",
            "LifeCycleDefinitionGUID=", "RevisionNamingSchemeGUID=", "",
            "[OutputGroup1]", "Name=", "Description=", f"TargetOutputMedium={container}",
            "VariantName=[No Variations]", "VariantScope=0", "CurrentConfigurationName=", "TargetPrinter=",
            "PrinterOptions=Record=PrinterOptions|Copies=1|Duplex=1|TrueTypeOptions=3|Collate=1|PrintWhat=1", "",
            "[PublishSettings]", "", "[GeneratedFilesSettings]"]
    doc = IniDoc("\r\n".join(head))
    add_container(doc, container)
    return doc


def apply(doc: IniDoc, specs: Dict[str, dict], container: str = "", output_folder: Optional[str] = None,
          board_document: Optional[str] = None) -> dict:
    """Write specs (kind -> settings) into doc: each into the first output of
    its kind (added when there is none), connected to the container. Returns
    what was done: the container used, and per kind the output's index,
    whether it was added and whether it was connected now."""
    for kind in specs:
        if kind not in KINDS:
            raise OutJobError(f"unknown output '{kind}': one of {', '.join(KINDS)}")
    if output_folder is not None:
        folder = str(output_folder).strip()
        if not folder or any(c in folder for c in "|\r\n"):
            raise OutJobError(f"output_folder '{output_folder}': a folder (relative to the project's folder, or "
                              "absolute), no '|' or line break")
        output_folder = folder
    if board_document is not None:
        board_document = _clean(board_document, "board_document")
    # worked on a copy, so a check that fails half way leaves doc as it was
    work = IniDoc(doc.text())
    result = _apply(work, specs, container, output_folder, board_document)
    doc.sections = work.sections
    return result


def _apply(doc: IniDoc, specs: Dict[str, dict], container: str, output_folder: Optional[str],
           board_document: Optional[str]) -> dict:
    mediums = doc.numbered(GROUP, "OutputMedium")
    added_container = False
    if container:
        container = _clean(container, "container")
        m = _container_index(doc, container)
        if m and doc.get(GROUP, f"OutputMedium{m}_Type") != "GeneratedFiles":
            raise OutJobError(f"container '{container}' is a {doc.get(GROUP, f'OutputMedium{m}_Type')} container, "
                              "not GeneratedFiles: it cannot hold Gerber, drill, BOM or pick and place files")
    else:
        m = next((i for i, _ in mediums if doc.get(GROUP, f"OutputMedium{i}_Type") == "GeneratedFiles"), 0)
        container = doc.get(GROUP, f"OutputMedium{m}") if m else "Generated Files"
    if not m:
        m = add_container(doc, container)
        added_container = True
    if output_folder is not None:
        set_output_folder(doc, m, output_folder)

    done = {}
    for kind, spec in specs.items():
        n = next((i for i, t in _outputs(doc) if t == KINDS[kind]["type"]), 0)
        added = not n
        if added:
            n = add_output(doc, kind)
        write_settings(doc, n, kind, spec)
        if board_document is not None and kind != "bom":
            doc.set(GROUP, f"OutputDocumentPath{n}", board_document)
        done[kind] = {"index": n, "name": doc.get(GROUP, f"OutputName{n}"), "added": added,
                      "connected_now": connect(doc, n, m)}
    return {"container": container, "container_index": m, "container_added": added_container, "outputs": done}


# --- Read back -----------------------------------------------------------

def compare(parsed: dict, specs: Dict[str, dict], done: dict, output_folder: Optional[str],
            board_document: Optional[str]) -> List[str]:
    """What the file as read back (outjob_parser.parse_outjob) does not hold
    of what was asked."""
    diffs = []
    outputs = {o["index"]: o for o in parsed["outputs"]}
    container = done["container"]
    c = next((c for c in parsed["containers"] if c["name"] == container), None)
    if c is None:
        return [f"container '{container}' is not in the file read back"]
    if output_folder is not None:
        if c.get("base_path") != output_folder:
            diffs.append(f"output folder: asked {output_folder}, the file has {c.get('base_path')}")
        if c.get("release_managed"):
            diffs.append("output folder: the container is still release managed")
    for kind, spec in specs.items():
        o = outputs.get(done["outputs"][kind]["index"])
        if o is None or o["type"] != KINDS[kind]["type"]:
            diffs.append(f"{kind}: no {KINDS[kind]['type']} output at its index in the file read back")
            continue
        if container not in o["connected_containers"]:
            diffs.append(f"{kind}: not connected to '{container}'")
        if board_document is not None and kind != "bom" and o.get("document_path") != board_document:
            diffs.append(f"{kind}: document asked {board_document}, the file has {o.get('document_path')}")
        got = {}
        if kind == "gerber":
            g = o.get("gerber") or {}
            if "units" in spec:
                got["units"] = (UNITS[spec["units"].lower()], g.get("units"))
            if "format" in spec:
                got["format"] = (spec["format"].split(":")[1], g.get("decimals"))
            if "zeroes" in spec:
                got["zeroes"] = (ZEROES[spec["zeroes"].lower()], g.get("zeroes"))
            if "origin" in spec:
                got["origin"] = (ORIGINS[spec["origin"].lower()], g.get("origin"))
            if "board_profile" in spec:
                got["board_profile"] = (bool(spec["board_profile"]), g.get("plot_board_profile"))
            if "layers" in spec:
                got["layers"] = (sorted(layer_ids(spec["layers"])), sorted(l["id"] for l in g.get("plotted_layers", [])))
        elif kind == "nc_drill":
            d = o.get("nc_drill") or {}
            current = "mm" if d.get("Units") == "Metric" else "inch"
            for key, value in drill_values(spec, current).items():
                got[key] = (value, d.get(key))
        elif kind == "pick_place":
            p = o.get("pick_place") or {}
            for key, value in pnp_values(spec).items():
                got[key] = (value, p.get(key))
        else:
            b = o.get("bom") or {}
            values = bom_values(spec)
            if "format" in spec:
                got["format"] = (spec["format"].lower(), b.get("format"))
            if "columns" in spec:
                got["columns"] = ([str(x).strip() for x in spec["columns"]], b.get("columns"))
            if "group_by" in spec:
                got["group_by"] = ([str(x).strip() for x in spec["group_by"]], b.get("group_by"))
            if "BatchMode" in values and b.get("open_exported"):
                diffs.append("bom: the file still opens the exported BOM after a run")
        for key, (asked, has) in got.items():
            if asked != has:
                diffs.append(f"{kind} {key}: asked {asked}, the file has {has}")
    return diffs
