package com.utc.alert.service;

import com.utc.alert.entity.AlertEvent;

public interface PriorityCalcService {

    int calculate(AlertEvent alertEvent);
}
