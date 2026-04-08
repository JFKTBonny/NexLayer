// order-service/src/main/java/com/app/Order.java
package com.app;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(nullable = false)
    private String product;

    @Column(nullable = false)
    private Integer quantity = 1;

    @Column(nullable = false)
    private BigDecimal price;

    @Enumerated(EnumType.STRING)
    private Status status = Status.pending;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    public enum Status { pending, confirmed, shipped, delivered }

    // Getters and Setters
    public Long getId()                        { return id; }
    public Long getUserId()                    { return userId; }
    public void setUserId(Long userId)         { this.userId = userId; }
    public String getProduct()                 { return product; }
    public void setProduct(String product)     { this.product = product; }
    public Integer getQuantity()               { return quantity; }
    public void setQuantity(Integer quantity)  { this.quantity = quantity; }
    public BigDecimal getPrice()               { return price; }
    public void setPrice(BigDecimal price)     { this.price = price; }
    public Status getStatus()                  { return status; }
    public void setStatus(Status status)       { this.status = status; }
    public LocalDateTime getCreatedAt()        { return createdAt; }
}