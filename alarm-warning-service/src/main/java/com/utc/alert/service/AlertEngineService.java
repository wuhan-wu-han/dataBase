package com.utc.alert.service;

import com.utc.alert.dto.kafka.KafkaMessage;

public interface AlertEngineService {

    void processMessage(KafkaMessage message);
}
