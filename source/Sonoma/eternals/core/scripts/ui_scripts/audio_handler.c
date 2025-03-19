#include <windows.h>
#include <mmdeviceapi.h>
#include <endpointvolume.h>
#include <audioclient.h>

typedef struct {
    IAudioEndpointVolume* volumeEndpoint;
    IMMDeviceEnumerator* deviceEnumerator;
    IMMDevice* device;
} AudioHandler;

static AudioHandler* audioHandler = NULL;

int initAudioHandler() {
    HRESULT hr;
    
    if (audioHandler != NULL) {
        return 0;
    }
    
    audioHandler = (AudioHandler*)malloc(sizeof(AudioHandler));
    if (!audioHandler) {
        return -1;
    }

    hr = CoInitialize(NULL);
    if (FAILED(hr)) {
        free(audioHandler);
        return -1;
    }

    hr = CoCreateInstance(&CLSID_MMDeviceEnumerator, NULL, CLSCTX_ALL,
                         &IID_IMMDeviceEnumerator, (void**)&audioHandler->deviceEnumerator);
    if (FAILED(hr)) {
        CoUninitialize();
        free(audioHandler);
        return -1;
    }

    hr = audioHandler->deviceEnumerator->lpVtbl->GetDefaultAudioEndpoint(
        audioHandler->deviceEnumerator, eRender, eConsole, &audioHandler->device);
    if (FAILED(hr)) {
        audioHandler->deviceEnumerator->lpVtbl->Release(audioHandler->deviceEnumerator);
        CoUninitialize();
        free(audioHandler);
        return -1;
    }

    hr = audioHandler->device->lpVtbl->Activate(audioHandler->device,
                                               &IID_IAudioEndpointVolume,
                                               CLSCTX_ALL,
                                               NULL,
                                               (void**)&audioHandler->volumeEndpoint);
    if (FAILED(hr)) {
        audioHandler->device->lpVtbl->Release(audioHandler->device);
        audioHandler->deviceEnumerator->lpVtbl->Release(audioHandler->deviceEnumerator);
        CoUninitialize();
        free(audioHandler);
        return -1;
    }

    return 0;
}

float getVolume() {
    float volume = 0.0f;
    if (audioHandler && audioHandler->volumeEndpoint) {
        audioHandler->volumeEndpoint->lpVtbl->GetMasterVolumeLevelScalar(
            audioHandler->volumeEndpoint, &volume);
    }
    return volume;
}

int setVolume(float volume) {
    if (volume < 0.0f) volume = 0.0f;
    if (volume > 1.0f) volume = 1.0f;
    
    if (audioHandler && audioHandler->volumeEndpoint) {
        HRESULT hr = audioHandler->volumeEndpoint->lpVtbl->SetMasterVolumeLevelScalar(
            audioHandler->volumeEndpoint, volume, NULL);
        return SUCCEEDED(hr) ? 0 : -1;
    }
    return -1;
}

int toggleMute() {
    BOOL muted;
    if (audioHandler && audioHandler->volumeEndpoint) {
        audioHandler->volumeEndpoint->lpVtbl->GetMute(audioHandler->volumeEndpoint, &muted);
        audioHandler->volumeEndpoint->lpVtbl->SetMute(audioHandler->volumeEndpoint, !muted, NULL);
        return 0;
    }
    return -1;
}

void cleanupAudioHandler() {
    if (audioHandler) {
        if (audioHandler->volumeEndpoint) {
            audioHandler->volumeEndpoint->lpVtbl->Release(audioHandler->volumeEndpoint);
        }
        if (audioHandler->device) {
            audioHandler->device->lpVtbl->Release(audioHandler->device);
        }
        if (audioHandler->deviceEnumerator) {
            audioHandler->deviceEnumerator->lpVtbl->Release(audioHandler->deviceEnumerator);
        }
        CoUninitialize();
        free(audioHandler);
        audioHandler = NULL;
    }
}
