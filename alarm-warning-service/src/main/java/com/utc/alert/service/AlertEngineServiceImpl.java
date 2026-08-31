package com.utc.alert.service;

import com.utc.alert.dto.kafka.KafkaMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class AlertEngineServiceImpl implements AlertEngineService {

    @Override
    public void processMessage(KafkaMessage message) {
        log.info("AlertEngine received message: eventId={}, eventType={}, deviceId={}",
                message.getEventId(), message.getEventType(), message.getDeviceId());
    }
}
