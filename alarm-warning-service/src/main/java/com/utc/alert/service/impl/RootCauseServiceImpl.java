package com.utc.alert.service.impl;

import com.utc.alert.common.enums.RootCauseType;
import com.utc.alert.dto.RootCauseResult;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.service.RootCauseService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
public class RootCauseServiceImpl implements RootCauseService {

    @Override
    public RootCauseResult analyze(KafkaMessage message) {
        if (message == null) {
            log.warn("RootCause analyze: message is null");
            return buildResult(RootCauseType.UNKNOWN);
        }

        log.info("RootCause analysis start: eventId={}, deviceType={}",
                message.getEventId(), message.getDeviceType());

        try {
            RootCauseResult result = doAnalyze(message);

            log.info("RootCause analysis done: eventId={}, rootCause={}",
                    message.getEventId(), result.getRootCauseType());

            return result;
        } catch (Exception e) {
            log.error("RootCause analysis failed, eventId={}", message.getEventId(), e);
            return buildResult(RootCauseType.UNKNOWN);
        }
    }

    private RootCauseResult doAnalyze(KafkaMessage message) {
        String deviceType = message.getDeviceType();
        Map<String, Object> metrics = message.getMetrics();

        if (deviceType == null || metrics == null || metrics.isEmpty()) {
            return buildResult(RootCauseType.UNKNOWN);
        }

        return switch (deviceType) {
            case "PRESSURE" -> analyzePressure(metrics);
            case "TEMPERATURE" -> analyzeTemperature(metrics);
            case "CH4" -> analyzeCh4(metrics);
            case "H2S" -> analyzeH2s(metrics);
            default -> buildResult(RootCauseType.UNKNOWN);
        };
    }

    private RootCauseResult analyzePressure(Map<String, Object> metrics) {
        if (metrics.containsKey("pressure")) {
            RootCauseResult result = buildResult(RootCauseType.PRESSURE_ABNORMAL);
            result.setRootCauseDesc("压力指标异常，需要检查管道压力状态。");
            return result;
        }
        return buildResult(RootCauseType.UNKNOWN);
    }

    private RootCauseResult analyzeTemperature(Map<String, Object> metrics) {
        if (metrics.containsKey("temperature")) {
            RootCauseResult result = buildResult(RootCauseType.TEMPERATURE_ABNORMAL);
            result.setRootCauseDesc("温度异常，需要检查设备运行状态。");
            return result;
        }
        return buildResult(RootCauseType.UNKNOWN);
    }

    private RootCauseResult analyzeCh4(Map<String, Object> metrics) {
        if (metrics.containsKey("ch4") || metrics.containsKey("ch4_concentration")) {
            RootCauseResult result = buildResult(RootCauseType.GAS_LEAK);
            result.setRootCauseDesc("燃气浓度异常，存在泄漏风险。");
            return result;
        }
        return buildResult(RootCauseType.UNKNOWN);
    }

    private RootCauseResult analyzeH2s(Map<String, Object> metrics) {
        RootCauseResult result = buildResult(RootCauseType.GAS_LEAK);
        result.setRootCauseDesc("硫化氢浓度异常，存在气体泄漏风险。");
        return result;
    }

    private RootCauseResult buildResult(RootCauseType type) {
        RootCauseResult result = new RootCauseResult();
        result.setRootCauseType(type.name());
        result.setRootCauseDesc(type.getDesc());
        return result;
    }
}
