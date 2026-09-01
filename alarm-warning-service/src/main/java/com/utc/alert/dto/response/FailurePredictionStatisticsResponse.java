package com.utc.alert.dto.response;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class FailurePredictionStatisticsResponse {

    private long totalDevices;
    private long highRiskCount;
    private long mediumRiskCount;
    private long lowRiskCount;
    private BigDecimal avgHealthScore;
    private BigDecimal avgRemainingLifeMonth;
}
