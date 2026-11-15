object MCPResidentForm: TMCPResidentForm
  Left = 40
  Top = 40
  Caption = 'altium-mcp resident'
  ClientHeight = 40
  ClientWidth = 200
  OnClose = MCPResidentFormClose
  object ResidentTimer: TTimer
    Enabled = False
    Interval = 100
    OnTimer = ResidentTimerTimer
    Left = 8
    Top = 8
  end
end
