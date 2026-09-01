package com.utc.alert.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("alert_event")
public class AlertEvent {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String alertEventCode;

    private String sourceEventId;

    private String source;

    private String deviceId;

    private String deviceType;

    private String zone;

    private String areaId;

    private String alertLevel;

    private String alertStatus;

    private String metricKey;

    private BigDecimal metricValue;

    private BigDecimal thresholdValue;

    private String rootCause;

    private String rootCauseDesc;

    private Integer priorityScore;

    private Long alertGroupId;

    private Integer mergedCount;

    private Long eventTimestamp;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
