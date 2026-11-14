object A30BridgeForm: TA30BridgeForm
  Left = 40
  Top = 40
  Caption = 'a30 bridge probe'
  ClientHeight = 40
  ClientWidth = 200
  OnClose = A30BridgeFormClose
  object BridgeTimer: TTimer
    Enabled = False
    Interval = 100
    OnTimer = BridgeTimerTimer
    Left = 8
    Top = 8
  end
end
