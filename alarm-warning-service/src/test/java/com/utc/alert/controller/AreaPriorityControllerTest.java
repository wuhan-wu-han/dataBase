package com.utc.alert.controller;

import com.utc.alert.dto.response.AreaPriorityResponse;
import com.utc.alert.service.AreaPriorityService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.util.List;

import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class AreaPriorityControllerTest {

    @Mock
    private AreaPriorityService areaPriorityService;

    @InjectMocks
    private AreaPriorityController areaPriorityController;

    private MockMvc mockMvc;

    @org.junit.jupiter.api.BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.standaloneSetup(areaPriorityController)
                .setControllerAdvice(new com.utc.alert.common.exception.GlobalExceptionHandler())
                .build();
    }

    @Test
    void getAllAreaPriorities_returnsList() throws Exception {
        AreaPriorityResponse response = new AreaPriorityResponse();
        response.setAreaId("AREA-A01");
        response.setAreaName("A区");
        response.setImportance(8);
        response.setPopulationWeight(new BigDecimal("1.5"));
        when(areaPriorityService.getAllAreaPriorities()).thenReturn(List.of(response));

        mockMvc.perform(get("/api/area-priority"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].areaId").value("AREA-A01"))
                .andExpect(jsonPath("$.data[0].importance").value(8));
    }

    @Test
    void getAllAreaPriorities_empty_returnsEmptyList() throws Exception {
        when(areaPriorityService.getAllAreaPriorities()).thenReturn(List.of());

        mockMvc.perform(get("/api/area-priority"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data").isEmpty());
    }
}
