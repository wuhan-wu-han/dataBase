package com.utc.alert.service;

import com.utc.alert.dto.RootCauseResult;
import com.utc.alert.dto.kafka.KafkaMessage;

public interface RootCauseService {

    RootCauseResult analyze(KafkaMessage message);
}
