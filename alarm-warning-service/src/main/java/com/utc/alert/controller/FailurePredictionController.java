package com.utc.alert.controller;

import com.utc.alert.common.result.Result;
import com.utc.alert.dto.request.FailurePredictionQueryRequest;
import com.utc.alert.dto.response.FailurePredictionResponse;
import com.utc.alert.dto.response.FailurePredictionStatisticsResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.service.FailurePredictionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/failure-predictions")
@RequiredArgsConstructor
public class FailurePredictionController {

    private final FailurePredictionService failurePredictionService;

    @GetMapping
    public Result<PageResponse<FailurePredictionResponse>> getPredictions(FailurePredictionQueryRequest request) {
        return Result.success(failurePredictionService.getPredictions(request));
    }

    @GetMapping("/{id}")
    public Result<FailurePredictionResponse> getPredictionById(@PathVariable Long id) {
        return Result.success(failurePredictionService.getPredictionById(id));
    }

    @PostMapping("/generate")
    public Result<FailurePredictionResponse> generatePrediction() {
        return Result.success(failurePredictionService.generatePrediction());
    }

    @GetMapping("/statistics")
    public Result<FailurePredictionStatisticsResponse> getStatistics() {
        return Result.success(failurePredictionService.getStatistics());
    }
}
