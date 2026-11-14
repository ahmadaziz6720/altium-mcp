Interface

Type
  TA30BridgeForm = class(TForm)
    BridgeTimer : TTimer;
    procedure BridgeTimerTimer(Sender : TObject);
    procedure A30BridgeFormClose(Sender : TObject; var Action : TCloseAction);
  end;

Var
  A30BridgeForm : TA30BridgeForm;
  A30Ticks : Integer;
  A30Served : Integer;
  A30Busy : Boolean;

Implementation

{$R *.DFM}

procedure A30Beat(S : String);
var L : TStringList;
begin
    L := TStringList.Create;
    L.Text := S;
    L.SaveToFile('C:\Users\Public\a30_probe\bridge_hb.txt');
    L.Free;
end;

procedure TA30BridgeForm.BridgeTimerTimer(Sender : TObject);
begin
    if A30Busy then Exit;
    A30Busy := True;
    A30Ticks := A30Ticks + 1;
    if FileExists('C:\Users\Public\altium_mcp\request.json') then
    begin
        Run;
        A30Served := A30Served + 1;
    end;
    A30Beat(IntToStr(A30Ticks) + ' ' + IntToStr(A30Served) + ' ' + FormatDateTime('hh:nn:ss.zzz', Now));
    if FileExists('C:\Users\Public\a30_probe\stop.txt') then
    begin
        BridgeTimer.Enabled := False;
        A30Beat('stopped ' + IntToStr(A30Ticks) + ' ' + IntToStr(A30Served));
        Close;
    end;
    A30Busy := False;
end;

procedure TA30BridgeForm.A30BridgeFormClose(Sender : TObject; var Action : TCloseAction);
begin
    Action := caFree;
end;

procedure StartResident;
begin
    A30Ticks := 0; A30Served := 0; A30Busy := False;
    A30BridgeForm.BridgeTimer.Enabled := True;
    A30BridgeForm.BorderStyle := bsNone;
    A30BridgeForm.Left := -32000;
    A30BridgeForm.Top := -32000;
    A30BridgeForm.Show;
end;

End.
