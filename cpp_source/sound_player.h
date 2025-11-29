#pragma once
#include <xaudio2.h>
#include <string>
#include <map>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>

class SoundPlayer {
public:
    SoundPlayer(const std::map<std::string, std::string>& sounds);
    ~SoundPlayer();

    void play(const std::string& key);
    void set_volume(const std::string& key, float volume);
    void volume_up(const std::string& key, float step);
    void volume_down(const std::string& key, float step);
    void set_master_volume(float volume);
    void master_volume_up(float step);
    void master_volume_down(float step);
    void set_max_volume(float max_vol);
    void set_min_volume(float min_vol);
    float get_max_volume(void);
    float get_min_volume(void);


private:
    struct SoundData {
        WAVEFORMATEX wfx{};
        std::vector<BYTE> buffer;
        float volume = 1.0f;
    };

    std::map<std::string, SoundData> sound_map;

    IXAudio2* engine = nullptr;
    IXAudio2MasteringVoice* master_voice = nullptr;

    std::queue<std::string> job_queue;
    std::mutex queue_mutex;
    std::condition_variable cv;
    bool running = true;

    std::thread worker;

    void worker_thread();
    bool load_wav(const std::string& path, SoundData& out);
};
