package com.utc.gateway;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Map;

/** 在统一入口执行 JWT 身份认证与基于路径的 RBAC 权限校验。 */
@Component
public class AuthGlobalFilter implements GlobalFilter, Ordered {
    private final ObjectMapper objectMapper;
    private final byte[] secret;

    public AuthGlobalFilter(ObjectMapper objectMapper,
                            @Value("${security.jwt-secret:change-this-rbac-secret-in-production}") String secret) {
        this.objectMapper = objectMapper;
        this.secret = secret.getBytes(StandardCharsets.UTF_8);
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getURI().getPath();
        if (HttpMethod.OPTIONS.equals(exchange.getRequest().getMethod()) || isPublic(path)) {
            return chain.filter(exchange);
        }

        String authorization = exchange.getRequest().getHeaders().getFirst("Authorization");
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            return reject(exchange, HttpStatus.UNAUTHORIZED, "请先登录");
        }

        final Map<String, Object> claims;
        try {
            claims = verify(authorization.substring(7));
        } catch (Exception ignored) {
            return reject(exchange, HttpStatus.UNAUTHORIZED, "登录状态已失效，请重新登录");
        }

        String required = requiredPermission(path, exchange.getRequest().getMethod());
        List<?> permissions = claims.get("permissions") instanceof List<?> list ? list : List.of();
        if (required != null && !permissions.contains("*") && !permissions.contains(required)) {
            return reject(exchange, HttpStatus.FORBIDDEN, "当前角色无权执行此操作");
        }

        ServerWebExchange authenticated = exchange.mutate().request(builder -> builder
            .header("X-User-Id", String.valueOf(claims.get("sub")))
            .header("X-Username", String.valueOf(claims.get("username"))))
            .build();
        return chain.filter(authenticated);
    }

    private boolean isPublic(String path) {
        return path.equals("/auth/login")
            || path.equals("/api/platform/auth/login")
            || path.equals("/actuator/health")
            || path.startsWith("/frontend/");
    }

    private Map<String, Object> verify(String token) throws Exception {
        String[] parts = token.split("\\.");
        if (parts.length != 3) throw new IllegalArgumentException("invalid token");
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret, "HmacSHA256"));
        byte[] expected = mac.doFinal((parts[0] + "." + parts[1]).getBytes(StandardCharsets.UTF_8));
        byte[] actual = Base64.getUrlDecoder().decode(pad(parts[2]));
        if (!MessageDigest.isEqual(expected, actual)) throw new IllegalArgumentException("bad signature");
        Map<String, Object> claims = objectMapper.readValue(
            Base64.getUrlDecoder().decode(pad(parts[1])), new TypeReference<>() {});
        Number exp = claims.get("exp") instanceof Number number ? number : null;
        if (exp == null || exp.longValue() <= Instant.now().getEpochSecond()) {
            throw new IllegalArgumentException("expired");
        }
        return claims;
    }

    private String pad(String value) {
        return value + "=".repeat((4 - value.length() % 4) % 4);
    }

    private String requiredPermission(String path, HttpMethod method) {
        boolean read = HttpMethod.GET.equals(method) || HttpMethod.HEAD.equals(method);
        if (path.startsWith("/api/gas-risk/")) return read ? "gas-risk:view" : "gas-risk:manage";
        if (path.startsWith("/api/gas-asset/")) return read ? "asset:view" : "asset:manage";
        if (path.startsWith("/api/road-hazard/")) return read ? "road-hazard:view" : "road-hazard:manage";
        if (path.startsWith("/api/alerts") || path.startsWith("/api/alert-rules")
            || path.startsWith("/api/alert-groups") || path.startsWith("/api/area-priorities")) {
            return read ? "alert:view" : "alert:manage";
        }
        if (path.startsWith("/api/failure")) return read ? "failure:view" : "failure:manage";
        if (path.startsWith("/auth/") || path.startsWith("/api/platform/auth/")) return null;
        if (path.startsWith("/api/platform/notifications")) {
            if (path.endsWith("/recipients") || path.endsWith("/send")) return "notification:send";
            if (path.endsWith("/retry")) return "notification:retry";
            return read ? "notification:view" : "notification:config";
        }
        if (path.startsWith("/api/platform/gis")) return read ? "gis:view" : "gis:manage";
        if (path.startsWith("/api/platform/risk")) return read ? "risk:view" : "risk:manage";
        if (path.startsWith("/api/platform/hazmat")) return read ? "hazmat:view" : "hazmat:manage";
        if (path.startsWith("/api/platform/tunnel")) return read ? "tunnel:view" : "tunnel:manage";
        if (path.startsWith("/api/platform/plan")) return read ? "plan:view" : "plan:manage";
        if (path.startsWith("/api/platform/asset-cost")) return read ? "asset-cost:view" : "asset-cost:manage";
        if (path.startsWith("/api/platform/workorder")) return read ? "work-order:view" : "work-order:manage";
        return null; // 未归类接口仍要求有效登录，不额外要求业务权限
    }

    private Mono<Void> reject(ServerWebExchange exchange, HttpStatus status, String message) {
        exchange.getResponse().setStatusCode(status);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);
        byte[] bytes;
        try {
            bytes = objectMapper.writeValueAsBytes(Map.of("code", status.value(), "message", message));
        } catch (Exception ignored) {
            bytes = "{\"message\":\"access denied\"}".getBytes(StandardCharsets.UTF_8);
        }
        DataBuffer buffer = exchange.getResponse().bufferFactory().wrap(bytes);
        return exchange.getResponse().writeWith(Mono.just(buffer));
    }

    @Override
    public int getOrder() {
        return -100;
    }
}

