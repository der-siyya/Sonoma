
class LanguageSelect
{
    protected Widget m_wRoot;
    protected ButtonWidget m_LanguageButton;
    protected ref array<ref LanguageOption> m_Languages;
    
    void LanguageSelect(Widget parent)
    {
        m_wRoot = parent;
        m_Languages = new array<ref LanguageOption>;
        
        m_LanguageButton = ButtonWidget.Cast(m_wRoot.FindAnyWidget("LanguageButton"));
        if (m_LanguageButton)
        {
            m_LanguageButton.SetHandler(this);
            LoadAvailableLanguages();
        }
    }
    
    void LoadAvailableLanguages()
    {
        m_Languages.Clear();
        array<string> languageFiles = new array<string>;
        string languagePath = "$profile:Languages";
        FindFileHandle handle = FindFile(languagePath + "/*.lang", languageFiles);
        
        foreach (string file: languageFiles)
        {
            string languageCode = file.Substring(0, file.Length() - 5);
            m_Languages.Insert(new LanguageOption(languageCode, GetLanguageDisplayName(languageCode)));
        }
    }
    
    void OnLanguageSelect(int index)
    {
        if (index >= 0 && index < m_Languages.Count())
        {
            string selectedLanguage = m_Languages.Get(index).GetCode();
            GetGame().SetLanguage(selectedLanguage);
            GetGame().GetCallQueue(CALL_CATEGORY_GUI).CallLater(GetGame().ReloadLanguage, 100, false);
        }
    }
    
    string GetLanguageDisplayName(string code)
    {
        switch (code)
        {
            case "en":
                return "English";
            case "fr":
                return "Français";
            case "de":
                return "Deutsch";
            case "es":
                return "Español";
            case "it":
                return "Italiano";
            case "pt":
                return "Português";
            case "ru":
                return "Русский";
            case "pl":
                return "Polski";
            default:
                return code.ToUpper();
        }
    }
    
    void ~LanguageSelect()
    {
        m_Languages.Clear();
    }
}

class LanguageOption
{
    protected string m_Code;
    protected string m_DisplayName;
    
    void LanguageOption(string code, string displayName)
    {
        m_Code = code;
        m_DisplayName = displayName;
    }
    
    string GetCode()
    {
        return m_Code;
    }
    
    string GetDisplayName()
    {
        return m_DisplayName;
    }
}
