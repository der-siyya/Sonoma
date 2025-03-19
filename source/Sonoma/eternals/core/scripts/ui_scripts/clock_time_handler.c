
class ClockTimeHandler
{
    private float m_LastUpdateTime;
    private const float UPDATE_INTERVAL = 1.0;
    
    void Init() 
    {
        m_LastUpdateTime = GetGame().GetTime();
        UpdateDateTime();
    }
    
    void UpdateDateTime() 
    {
        float currentTime = GetGame().GetTime();
        
        if (currentTime - m_LastUpdateTime >= UPDATE_INTERVAL) 
        {
            string timeStr = FormatTimeString();
            string dateStr = FormatDateString();
            
            UpdateTimeDisplay(timeStr);
            UpdateDateDisplay(dateStr);
            
            m_LastUpdateTime = currentTime;
        }
    }
    
    private string FormatTimeString() 
    {
        int hour = GetGame().GetHour();
        int minute = GetGame().GetMinute();
        return string.Format("%02d:%02d", hour, minute);
    }
    
    private string FormatDateString() 
    {
        int day = GetGame().GetDay();
        int month = GetGame().GetMonth();
        int year = GetGame().GetYear();
        return string.Format("%02d/%02d/%04d", day, month, year);
    }
    
    private void UpdateTimeDisplay(string time) 
    {
        Widget timeWidget = GetGame().GetUIManager().GetWidget("TimeDisplay");
        if (timeWidget) 
        {
            TextWidget txt = TextWidget.Cast(timeWidget);
            txt.SetText(time);
        }
    }
    
    private void UpdateDateDisplay(string date) 
    {
        Widget dateWidget = GetGame().GetUIManager().GetWidget("DateDisplay");
        if (dateWidget) 
        {
            TextWidget txt = TextWidget.Cast(dateWidget);
            txt.SetText(date);
        }
    }
}
