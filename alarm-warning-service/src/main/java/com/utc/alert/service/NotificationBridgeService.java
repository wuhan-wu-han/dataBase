package com.utc.alert.service;

import com.utc.alert.entity.AlertEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/**
 * 告警服务与统一通知服务之间的轻量桥接。
 * 网络调用异步执行，通知服务故障不会阻塞告警入库。
 */
@Slf4j
@Service
public class NotificationBridgeService {

    private static final Set<String> AUTO_LEVELS = Set.of("ORANGE", "RED");
    private final RestClient client;
    private final String internalToken;
    private final boolean enabled;

    public NotificationBridgeService(
            @Value("${notification.platform-base-url:http://platform-api:8000}") String platformBaseUrl,
            @Value("${notification.internal-token:change-notification-internal-token}") String internalToken,
            @Value("${notification.auto-enabled:false}") boolean enabled) {
        this.client = RestClient.builder().baseUrl(platformBaseUrl).build();
        this.internalToken = internalToken;
        this.enabled = enabled;
    }

    @Async
    public void enqueue(AlertEvent event) {
        if (!enabled || event == null || !AUTO_LEVELS.contains(event.getAlertLevel())) {
            return;
        }
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("alertId", event.getAlertEventCode());
        payload.put("alertLevel", event.getAlertLevel());
        payload.put("title", event.getRootCauseDesc() != null ? event.getRootCauseDesc() : event.getMetricKey() + " 指标异常");
        payload.put("deviceId", event.getDeviceId());
        payload.put("deviceType", event.getDeviceType());
        payload.put("areaId", event.getAreaId());
        payload.put("metricKey", event.getMetricKey());
        payload.put("metricValue", event.getMetricValue() == null ? null : event.getMetricValue().toPlainString());
        payload.put("thresholdValue", event.getThresholdValue() == null ? null : event.getThresholdValue().toPlainString());
        payload.put("eventTimestamp", event.getEventTimestamp());
        try {
            client.post()
                    .uri("/notifications/dispatch-alert")
                    .header("X-Notification-Internal-Token", internalToken)
                    .body(payload)
                    .retrieve()
                    .toBodilessEntity();
        } catch (Exception exception) {
            log.warn("Automatic notification enqueue failed, alertEventCode={}: {}",
                    event.getAlertEventCode(), exception.getMessage());
        }
    }
}
