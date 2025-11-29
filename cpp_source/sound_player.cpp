#include "sound_player.h"
#include <fstream>
#include <iostream>
#include <mmreg.h>
#include <cstring>

float g_volume_max_value = 2.0f;
float g_volume_min_value = 0.0f;

void SoundPlayer::set_max_volume(float max_vol) {
    g_volume_max_value = max_vol;
}

void SoundPlayer::set_min_volume(float min_vol) {
    g_volume_min_value = min_vol;
}

float SoundPlayer::get_max_volume() {
    return g_volume_max_value;
}

float SoundPlayer::get_min_volume() {
    return g_volume_min_value;
}

bool SoundPlayer::load_wav(const std::string& path, SoundData& out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;

    char riff[4];
    f.read(riff, 4);
    if (memcmp(riff, "RIFF", 4) != 0) return false;

    f.ignore(4); // chunk size

    char wave[4];
    f.read(wave, 4);
    if (memcmp(wave, "WAVE", 4) != 0) return false;

    char fmt[4];
    f.read(fmt, 4);
    uint32_t fmt_size = 0;
    f.read(reinterpret_cast<char*>(&fmt_size), 4);
    f.read(reinterpret_cast<char*>(&out.wfx), fmt_size);

    // find "data" chunk
    char chunk_id[4];
    f.read(chunk_id, 4);
    while (memcmp(chunk_id, "data", 4) != 0) {
        uint32_t skip_size;
        f.read(reinterpret_cast<char*>(&skip_size), 4);
        f.ignore(skip_size);
        f.read(chunk_id, 4);
    }

    uint32_t data_size = 0;
    f.read(reinterpret_cast<char*>(&data_size), 4);

    out.buffer.resize(data_size);
    f.read(reinterpret_cast<char*>(out.buffer.data()), data_size);

    return true;
}

SoundPlayer::SoundPlayer(const std::map<std::string, std::string>& sounds) {
    CoInitializeEx(nullptr, COINIT_MULTITHREADED);

    if (FAILED(XAudio2Create(&engine, 0))) {
        throw std::runtime_error("XAudio2Create failed");
    }

    if (FAILED(engine->CreateMasteringVoice(&master_voice))) {
        throw std::runtime_error("CreateMasteringVoice failed");
    }

    // preload all wav files
    for (auto& kv : sounds) {
        SoundData sd;
        if (!load_wav(kv.second, sd)) {
            std::cerr << "Failed to load: " << kv.second << "\n";
            continue;
        }
        sound_map[kv.first] = std::move(sd);
    }

    worker = std::thread(&SoundPlayer::worker_thread, this);
}

SoundPlayer::~SoundPlayer() {
    {
        std::lock_guard<std::mutex> lock(queue_mutex);
        running = false;
    }
    cv.notify_all();

    if (worker.joinable()) worker.join();

    if (master_voice) master_voice->DestroyVoice();
    if (engine) engine->Release();

    CoUninitialize();
}

void SoundPlayer::play(const std::string& key) {
    std::lock_guard<std::mutex> lock(queue_mutex);
    job_queue.push(key);
    cv.notify_one();
}

void SoundPlayer::set_volume(const std::string& key, float vol) {
    if (sound_map.count(key))
        sound_map[key].volume = vol;
    std::cout << "the " << key << " volume is " << vol << std::endl;
}

void SoundPlayer::set_master_volume(float vol) {
    if (master_voice)
        master_voice->SetVolume(vol);
    std::cout << "the master volume is " << vol << std::endl;
}

void SoundPlayer::volume_up(const std::string& key, float step = 0.1f) {
    if (sound_map.count(key)) {
        float& vol = sound_map[key].volume;
        vol += step;
        if (vol > g_volume_max_value) vol = g_volume_max_value;
        std::cout << "The " << key << " volume increased to " << vol << std::endl;
    }
}

void SoundPlayer::volume_down(const std::string& key, float step = 0.1f) {
    if (sound_map.count(key)) {
        float& vol = sound_map[key].volume;
        vol -= step;
        if (vol < g_volume_min_value) vol = g_volume_min_value;
        std::cout << "The " << key << " volume decreased to " << vol << std::endl;
    }
}

void SoundPlayer::master_volume_up(float step = 0.1f) {
    if (master_voice) {
        float current_vol;
        master_voice->GetVolume(&current_vol);
        current_vol += step;
        if (current_vol > g_volume_max_value) current_vol = g_volume_max_value;
        master_voice->SetVolume(current_vol);
        std::cout << "Master volume increased to " << current_vol << std::endl;
    }
}

void SoundPlayer::master_volume_down(float step = 0.1f) {
    if (master_voice) {
        float current_vol;
        master_voice->GetVolume(&current_vol);
        current_vol -= step;
        if (current_vol < g_volume_min_value) current_vol = g_volume_min_value;
        master_voice->SetVolume(current_vol);
        std::cout << "Master volume decreased to " << current_vol << std::endl;
    }
}


void SoundPlayer::worker_thread() {
    while (true) {
        std::string key;

        {
            std::unique_lock<std::mutex> lock(queue_mutex);
            cv.wait(lock, [&] { return !job_queue.empty() || !running; });

            if (!running && job_queue.empty())
                break;

            key = job_queue.front();
            job_queue.pop();
        }

        auto it = sound_map.find(key);
        if (it == sound_map.end())
            continue;

        SoundData& sd = it->second;

        IXAudio2SourceVoice* voice = nullptr;
        if (FAILED(engine->CreateSourceVoice(&voice, &sd.wfx)))
            continue;

        XAUDIO2_BUFFER buf = { 0 };
        buf.AudioBytes = (UINT32)sd.buffer.size();  // eliminates your warning
        buf.pAudioData = sd.buffer.data();
        buf.Flags = XAUDIO2_END_OF_STREAM;

        voice->SetVolume(sd.volume);
        voice->SubmitSourceBuffer(&buf);
        voice->Start(0);
    }
}
