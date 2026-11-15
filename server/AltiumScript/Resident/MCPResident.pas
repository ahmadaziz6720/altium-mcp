Interface

// The resident bridge (A30): a form that stays in Altium with a timer, so a
// command needs no script launch, which brings Altium to the front and costs
// about 2 s. resident.py copies this unit, with %TAG% and %DIR% filled in,
// into a script project beside the bridge's own units and starts it once
// with ScriptingSystem:RunScript; the form outlives that script.
//
// Each tick: a stop file closes it; a take file the server writes beside
// request.json, deleted here, is the claim on the request (the server reads
// a take file it can still delete as a request not claimed, and launches the
// bridge as before); the caption carries the build's tag and the time once a
// second, the heartbeat the server reads with GetWindowText, never a file.

Type
  TMCPResidentForm = class(TForm)
    ResidentTimer : TTimer;
    procedure ResidentTimerTimer(Sender : TObject);
    procedure MCPResidentFormClose(Sender : TObject; var Action : TCloseAction);
  end;

Var
  MCPResidentForm : TMCPResidentForm;
  ResidentBusy : Boolean;
  ResidentBeat : Double;

Implementation

{$R *.DFM}

procedure ResidentHeartbeat(Form : TMCPResidentForm);
begin
    ResidentBeat := Now;
    Form.Caption := 'altium-mcp resident %TAG% ' + FormatDateTime('yyyymmddhhnnss', Now);
end;

procedure TMCPResidentForm.ResidentTimerTimer(Sender : TObject);
begin
    // A command served here can open a modal loop (an Altium message), in
    // which this timer fires again
    if ResidentBusy then Exit;
    ResidentBusy := True;
    if FileExists('%DIR%stop') then
    begin
        ResidentTimer.Enabled := False;
        Caption := 'altium-mcp resident %TAG% stopped';
        Close;
        Exit;
    end;
    if FileExists('%DIR%take') then
        if DeleteFile('%DIR%take') then
        begin
            Run;
            ResidentBeat := 0;
        end;
    if Now - ResidentBeat >= 1 / 86400 then
        ResidentHeartbeat(MCPResidentForm);
    ResidentBusy := False;
end;

procedure TMCPResidentForm.MCPResidentFormClose(Sender : TObject; var Action : TCloseAction);
begin
    Action := caFree;
end;

// The form must stay shown: a form never shown, or hidden again, is freed
// when this script ends. Off screen and borderless, it is not seen.
procedure StartResident;
begin
    ResidentBusy := False;
    MCPResidentForm.BorderStyle := bsNone;
    MCPResidentForm.Left := -32000;
    MCPResidentForm.Top := -32000;
    ResidentHeartbeat(MCPResidentForm);
    MCPResidentForm.ResidentTimer.Enabled := True;
    MCPResidentForm.Show;
end;

End.
