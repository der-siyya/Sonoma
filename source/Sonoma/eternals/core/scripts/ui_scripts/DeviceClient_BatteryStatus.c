#include <windows.h>
#include <strsafe.h>

typedef struct {
    int batteryPercentage;
    BOOL isCharging;
    BOOL hasBattery;
} BatteryStatus;

BatteryStatus GetBatteryStatus() {
    BatteryStatus status = {0};
    SYSTEM_POWER_STATUS powerStatus;

    if (GetSystemPowerStatus(&powerStatus)) {
        status.hasBattery = (powerStatus.BatteryFlag != 128);
        status.isCharging = (powerStatus.ACLineStatus == 1);
        
        if (powerStatus.BatteryLifePercent != 255) {
            status.batteryPercentage = powerStatus.BatteryLifePercent;
        } else {
            status.batteryPercentage = -1;
        }
    }

    return status;
}

void UpdateBatteryStatusUI() {
    BatteryStatus status = GetBatteryStatus();
    
    if (!status.hasBattery) {
        // Handle case where no battery is present
        return;
    }

    // Update UI elements based on battery status
    char statusText[64];
    if (status.isCharging) {
        StringCchPrintfA(statusText, 64, "Charging: %d%%", status.batteryPercentage);
    } else {
        StringCchPrintfA(statusText, 64, "Battery: %d%%", status.batteryPercentage);
    }

    // TODO: Update the UI elements with statusText
}
