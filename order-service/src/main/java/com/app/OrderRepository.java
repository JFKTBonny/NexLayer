// order-service/src/main/java/com/app/OrderRepository.java
package com.app;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByUserId(Long userId);
    List<Order> findByStatus(Order.Status status);
}