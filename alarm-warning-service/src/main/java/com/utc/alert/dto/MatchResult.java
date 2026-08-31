package com.utc.alert.dto;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class MatchResult {

    private String ruleCode;

    private String ruleName;

    private String alertLevel;

    private String metricKey;

    private BigDecimal metricValue;

    private BigDecimal thresholdValue;

    private String deviceType;

    private String areaId;
}
