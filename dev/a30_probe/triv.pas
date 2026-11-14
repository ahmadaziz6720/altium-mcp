procedure Run;
var L : TStringList;
begin
    L := TStringList.Create;
    L.Text := 'ok';
    L.SaveToFile('C:\Users\Public\a30_probe\triv.txt');
    L.Free;
end;
