package com.utc.alert.service;

import com.utc.alert.entity.AlertEvent;

import java.util.Optional;

public interface AlertDedupService {

    Optional<Long> tryMerge(AlertEvent alertEvent);
}
