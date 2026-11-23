# Recipes for `run_altium_script`

Jobs no tool does, by the codes of `open_items.md`. Every script here is, word for word
but its placeholders, one that a live test ran through `run_altium_script` in Altium
Designer 25 and passed with; each section names that test and what it did not show. No
script here was composed from a list of API calls: where only the calls are known, there is
no recipe (the list at the end). A section marked *No script* gives the step or tool call
that was used instead.

How to use one:

- Put your values in place of `<project>`, `<sheet>`, `<designator>` and `<kind>`: full
  long paths, and a quote inside a value doubled (`'` as `''`).
- Call `run_altium_script(script="<the script, filled in>")`. No other argument is needed.
- A script that removes an object sends `SCHM_PrimitiveRegistration` naming that object,
  one notice for each. Without it the project compile keeps the object, and the compile
  tools report success with it (A48 b).

## A55 - a project's documents and unsaved flag, by path

The project must be open in Altium (A62 opens it); it need not be focused. Reads only.

Result: a first line `True` or `False` (the project file has unsaved changes), then one
line per document. It gives no parameters, no variants and no state of each document.
`get_project_components` and `get_erc_violations` take a `project_path` themselves.

Proved by: `test_live_pcblib_from_board` (`project_state`). Reading by path with another
project focused: the same calls in `test_live_project_setup` (`project_documents`).

```pascal
var
    P : IProject;
    I : Integer;
    S : String;
begin
P := GetWorkspace.DM_GetProjectFromPath('<project>');
S := BoolToStr(Client.GetDocumentByPath(P.DM_ProjectFullPath).Modified, True) + #13#10;
for I := 0 to P.DM_LogicalDocumentCount - 1 do
    S := S + P.DM_LogicalDocuments(I).DM_FullPath + #13#10;
ResultText := S;
end;
```

## A56 (b) - the footprint library a placed part links to

The sheet must be open. One designator per call. Reads only.

Result: one line per model, `type|name|parameters`. Of the `PCBLIB` lines, the one with
`ISCURRENT=T` is the part's footprint, and `MODELDATAFILE0` is its library; none means a
link by name only. It does not say whether that library holds the footprint.

Proved by: `test_live_symbol_footprint` (`read_models`) on a placed part, for the model's
name and current mark, and `test_live_set_footprint` (the same script, `read_model_list`)
for `MODELDATAFILE0` on a placed part: the library `edit_schematic`'s `set_footprint` linked
it to, checked against the saved sheet's record. To set the footprint and its library, that
op.

```pascal
var
    D : ISch_Document;
    It, It2 : ISch_Iterator;
    C : ISch_Component;
    Im : ISch_Implementation;
    S : String;
    Found : Boolean;
begin
D := SchServer.GetSchDocumentByPath('<sheet>');
It := D.SchIterator_Create;

It.AddFilter_ObjectSet(MkSet(eSchComponent));
S := '';
Found := False;
C := It.FirstSchObject;
while C <> nil do
begin
  if (C.LibReference = '<designator>') or (C.Designator.Text = '<designator>') then
  begin
    Found := True;
    It2 := C.SchIterator_Create;
    It2.AddFilter_ObjectSet(MkSet(eImplementation));
    Im := It2.FirstSchObject;
    while Im <> nil do
    begin
      S := S + Im.ModelType + '|' + Im.ModelName + '|' + Im.ExportToParameters + #13#10;
      Im := It2.NextSchObject;
    end;
    C.SchIterator_Destroy(It2);
  end;
  C := It.NextSchObject;
end;
D.SchIterator_Destroy(It);
if not Found then S := 'NOT FOUND';
ResultText := S;
end;
```

## A52 - an object removed from a sheet, the compile told (in part)

Changes the sheet. It removes the **last** object of `<kind>` in the iterator's order, not
one you choose, and one per call. `<kind>` is `eNoERC` or `eSchComponent`, the two proved,
and the sheet must hold one: the script was never run on a sheet with none. It
saves nothing and does not mark the sheet modified.

Not covered: a whole sheet cleared, a sheet taken out of its project, its file deleted.

Proved by: `test_live_compile_refresh` (`remove_by_script`, with the notice): the next
compile held neither the marker nor the part.

```pascal
var
  Doc, It, O, Found : IDispatch;
begin
  Doc := OpenSchDoc('<sheet>');
  It := Doc.SchIterator_Create;
  It.AddFilter_ObjectSet(MkSet(<kind>));
  O := It.FirstSchObject;
  while O <> nil do
  begin
    Found := O;
    O := It.NextSchObject;
  end;
  Doc.SchIterator_Destroy(It);
  SchServer.ProcessControl.PreProcess(Doc, '');
  Doc.RemoveSchObject(Found);
  SchServer.RobotManager.SendMessage(Doc.I_ObjectAddress, c_BroadCast, SCHM_PrimitiveRegistration, Found.I_ObjectAddress);
  SchServer.ProcessControl.PostProcess(Doc, '');
  ResultText := 'removed';
end;
```

## A62 - a project opened by path (in part: not an option changed)

Use this, not `Client.OpenDocument('PrjPcb', ...)`, which left a project out of the
workspace. Result: the project's path as Altium has it.

Not covered: changing an option. Sessions saved and closed the project first, edited the
`.PrjPcb` (Altium writes LF only: add no CR), then opened it again by
`get_erc_violations(project_path=...)`. No proved script for that close is recorded, and
this script was not shown to read a file edited while the project was open.

Proved by: the live tests' `open_project` (`server/tests/live_altium.py`).

```pascal
Obj1 := GetWorkspace.DM_OpenProject('<project>', True);
ResultText := Obj1.DM_ProjectFullPath;
```

## A34 (f) - stop the resident bridge

*No script*, and no `run_altium_script` call: the bridge closes on a file.

1. `get_server_status`: take the `tag` of each entry in `resident_bridge.windows`.
2. Write a file named `stop`, its text `stop`, in
   `C:\Users\Public\altium_mcp\resident\<tag>\`.

The form closes within about 3 s; `get_server_status` then lists no such window. The next
tool call that uses the bridge starts it again.

Proved by: sessions that did it by hand, and `test_live_resident` (`stop_all_residents`).

## A51 - net labels with a justification

*No script.* Leave the labels out of `build_schematic` and add them in one `edit_schematic`
call after it, an `add_net_label` op each, with its `justification` (0 to 8).

Proved by: a session that drew nine sheets so.

## A67 - what three descriptions leave out

- (a) *No script.* `get_component_data` reads the board only. A schematic's parts are read
  by `get_project_components` or `get_schematic_data`.
- (b) *No script.* `edit_schematic`'s `add_power_port` shows the net name by default. On a
  sheet whose ports hide it, pass `"show_net_name": false`.
- (c) An object to act on later is kept in an `IDispatch` variable, as `Found` in A52's
  script, never in a `TStringList` by `AddObject`: read back it cannot be called, and a
  removal with it removes nothing.

## A69 (d) - a part swapped for another symbol (in part)

*No script.* One `edit_schematic` call per sheet: `delete_component`, `place_component` at
the old origin (moved by the difference of the two symbols' origins), then `move_text` for
the Designator and Comment. Compare the pins' nets after it.

Proved by: sessions that swapped parts so, the netlist unchanged.

## No proved script

A47 (sheet size, title block, parameters), A54 (the netlist), A59 (sheet symbols, ports,
harnesses), A63 (library parts copied, deleted, extracted), A64 (a footprint edited), A65
(a symbol's colours, Comment, pins) and A69 (a) to (c). `open_items.md` keeps the calls
sessions named for each, and what is missing. A script written from those calls is not
proved: read its result back, from the saved file where it saves one.
