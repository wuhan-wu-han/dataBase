package com.utc.alert.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("area_priority")
public class AreaPriority {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String areaId;

    private String areaName;

    private Integer importance;

    private BigDecimal populationWeight;

    private String description;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
