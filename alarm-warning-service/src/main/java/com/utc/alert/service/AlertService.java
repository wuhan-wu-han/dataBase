package com.utc.alert.service;

import com.utc.alert.dto.request.AlertQueryRequest;
import com.utc.alert.dto.request.UpdateAlertStatusRequest;
import com.utc.alert.dto.response.AlertResponse;
import com.utc.alert.dto.response.PageResponse;

public interface AlertService {

    PageResponse<AlertResponse> getAlerts(AlertQueryRequest request);

    AlertResponse getAlertById(Long id);

    AlertResponse updateAlertStatus(Long id, UpdateAlertStatusRequest request);
}
