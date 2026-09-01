package com.utc.alert.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.utc.alert.common.ErrorCode;
import com.utc.alert.common.exception.BusinessException;
import com.utc.alert.dto.request.FailurePredictionQueryRequest;
import com.utc.alert.dto.response.FailurePredictionResponse;
import com.utc.alert.dto.response.FailurePredictionStatisticsResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.entity.FailurePrediction;
import com.utc.alert.mapper.AlertEventMapper;
import com.utc.alert.mapper.FailurePredictionMapper;
import com.utc.alert.service.FailurePredictionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class FailurePredictionServiceImpl implements FailurePredictionService {

    private final FailurePredictionMapper failurePredictionMapper;
    private final AlertEventMapper alertEventMapper;

    @Override
    public PageResponse<FailurePredictionResponse> getPredictions(FailurePredictionQueryRequest request) {
        Page<FailurePrediction> page = new Page<>(request.getPage(), request.getSize());

        LambdaQueryWrapper<FailurePrediction> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(request.getPredictionLevel())) {
            wrapper.eq(FailurePrediction::getPredictionLevel, request.getPredictionLevel());
        }
        wrapper.orderByDesc(FailurePrediction::getPredictionTime);

        Page<FailurePrediction> result = failurePredictionMapper.selectPage(page, wrapper);

        List<FailurePredictionResponse> records = result.getRecords().stream()
                .map(this::toResponse)
                .collect(Collectors.toList());

        return PageResponse.of(result, records);
    }

    @Override
    public FailurePredictionResponse getPredictionById(Long id) {
        FailurePrediction prediction = failurePredictionMapper.selectById(id);
        if (prediction == null) {
            throw new BusinessException(ErrorCode.PREDICTION_NOT_FOUND);
        }
        return toResponse(prediction);
    }

    @Override
    public FailurePredictionResponse generatePrediction() {
        List<AlertEvent> allEvents = alertEventMapper.selectList(new LambdaQueryWrapper<>());

        Map<String, List<AlertEvent>> deviceEvents = allEvents.stream()
                .collect(Collectors.groupingBy(AlertEvent::getDeviceId));

        if (deviceEvents.isEmpty()) {
            log.info("无预警事件数据，跳过预测生成");
            return null;
        }

        FailurePrediction latest = null;

        for (Map.Entry<String, List<AlertEvent>> entry : deviceEvents.entrySet()) {
            String deviceId = entry.getKey();
            List<AlertEvent> events = entry.getValue();

            int alertCount = events.size();
            String deviceType = events.get(0).getDeviceType();
            String areaId = events.get(0).getAreaId();

            long redCount = events.stream().filter(e -> "RED".equals(e.getAlertLevel())).count();
            long orangeCount = events.stream().filter(e -> "ORANGE".equals(e.getAlertLevel())).count();

            int severityWeight = (int) (redCount * 15 + orangeCount * 8);

            BigDecimal healthScore = BigDecimal.valueOf(Math.max(0, 100 - alertCount * 5 - severityWeight))
                    .setScale(2, RoundingMode.HALF_UP);

            BigDecimal riskScore = BigDecimal.valueOf(Math.min(100, alertCount * 6 + severityWeight))
                    .setScale(2, RoundingMode.HALF_UP);

            BigDecimal failureProbability = BigDecimal.valueOf(
                    Math.min(100, Math.max(0, (100 - healthScore.doubleValue()) * 0.8 + riskScore.doubleValue() * 0.2))
            ).setScale(2, RoundingMode.HALF_UP);

            int remainingLifeMonth = Math.max(1, (int) (healthScore.doubleValue() / 3.0));

            String predictionLevel;
            if (failureProbability.doubleValue() >= 60) {
                predictionLevel = "CRITICAL";
            } else if (failureProbability.doubleValue() >= 40) {
                predictionLevel = "HIGH";
            } else if (failureProbability.doubleValue() >= 20) {
                predictionLevel = "MEDIUM";
            } else {
                predictionLevel = "LOW";
            }

            FailurePrediction prediction = new FailurePrediction();
            prediction.setDeviceId(deviceId);
            prediction.setDeviceType(deviceType);
            prediction.setAreaId(areaId);
            prediction.setHealthScore(healthScore);
            prediction.setRiskScore(riskScore);
            prediction.setFailureProbability(failureProbability);
            prediction.setRemainingLifeMonth(remainingLifeMonth);
            prediction.setPredictionLevel(predictionLevel);
            prediction.setPredictionTime(LocalDateTime.now());

            failurePredictionMapper.insert(prediction);
            latest = prediction;

            log.info("设备 {} 预测生成完成: health={}, risk={}, failure={}, life={}月, level={}",
                    deviceId, healthScore, riskScore, failureProbability, remainingLifeMonth, predictionLevel);
        }

        return latest != null ? toResponse(latest) : null;
    }

    @Override
    public FailurePredictionStatisticsResponse getStatistics() {
        List<FailurePrediction> all = failurePredictionMapper.selectList(
                new LambdaQueryWrapper<FailurePrediction>()
                        .orderByDesc(FailurePrediction::getPredictionTime)
        );

        Map<String, List<FailurePrediction>> latestByDevice = all.stream()
                .collect(Collectors.groupingBy(FailurePrediction::getDeviceId));

        List<FailurePrediction> latestList = latestByDevice.values().stream()
                .map(list -> list.stream()
                        .reduce((a, b) -> a.getPredictionTime().isAfter(b.getPredictionTime()) ? a : b)
                        .orElse(null))
                .filter(p -> p != null)
                .collect(Collectors.toList());

        FailurePredictionStatisticsResponse stats = new FailurePredictionStatisticsResponse();
        stats.setTotalDevices(latestList.size());
        stats.setHighRiskCount(latestList.stream()
                .filter(p -> "HIGH".equals(p.getPredictionLevel()) || "CRITICAL".equals(p.getPredictionLevel()))
                .count());
        stats.setMediumRiskCount(latestList.stream()
                .filter(p -> "MEDIUM".equals(p.getPredictionLevel()))
                .count());
        stats.setLowRiskCount(latestList.stream()
                .filter(p -> "LOW".equals(p.getPredictionLevel()))
                .count());

        if (!latestList.isEmpty()) {
            BigDecimal totalHealth = latestList.stream()
                    .map(FailurePrediction::getHealthScore)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            stats.setAvgHealthScore(totalHealth.divide(
                    BigDecimal.valueOf(latestList.size()), 2, RoundingMode.HALF_UP));

            BigDecimal totalLife = latestList.stream()
                    .map(p -> BigDecimal.valueOf(p.getRemainingLifeMonth()))
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            stats.setAvgRemainingLifeMonth(totalLife.divide(
                    BigDecimal.valueOf(latestList.size()), 2, RoundingMode.HALF_UP));
        } else {
            stats.setAvgHealthScore(BigDecimal.ZERO);
            stats.setAvgRemainingLifeMonth(BigDecimal.ZERO);
        }

        return stats;
    }

    private FailurePredictionResponse toResponse(FailurePrediction prediction) {
        FailurePredictionResponse response = new FailurePredictionResponse();
        response.setId(prediction.getId());
        response.setDeviceId(prediction.getDeviceId());
        response.setDeviceType(prediction.getDeviceType());
        response.setAreaId(prediction.getAreaId());
        response.setHealthScore(prediction.getHealthScore());
        response.setRiskScore(prediction.getRiskScore());
        response.setFailureProbability(prediction.getFailureProbability());
        response.setRemainingLifeMonth(prediction.getRemainingLifeMonth());
        response.setPredictionLevel(prediction.getPredictionLevel());
        response.setPredictionTime(prediction.getPredictionTime());
        response.setCreatedAt(prediction.getCreatedAt());
        return response;
    }
}
