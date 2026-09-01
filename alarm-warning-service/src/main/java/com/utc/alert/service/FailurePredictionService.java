package com.utc.alert.service;

import com.utc.alert.dto.request.FailurePredictionQueryRequest;
import com.utc.alert.dto.response.FailurePredictionResponse;
import com.utc.alert.dto.response.FailurePredictionStatisticsResponse;
import com.utc.alert.dto.response.PageResponse;

public interface FailurePredictionService {

    PageResponse<FailurePredictionResponse> getPredictions(FailurePredictionQueryRequest request);

    FailurePredictionResponse getPredictionById(Long id);

    FailurePredictionResponse generatePrediction();

    FailurePredictionStatisticsResponse getStatistics();
}
