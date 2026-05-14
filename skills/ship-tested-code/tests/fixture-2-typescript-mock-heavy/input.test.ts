import { describe, it, expect, vi, beforeEach } from "vitest";
import { CheckoutService } from "./checkout";

describe("CheckoutService", () => {
  let mockCart: any;
  let mockPricer: any;
  let mockInventory: any;
  let mockPaymentGateway: any;
  let mockNotifier: any;
  let mockAuditLog: any;
  let mockOrderRepo: any;
  let mockMetrics: any;
  let service: CheckoutService;

  beforeEach(() => {
    mockCart = { getItems: vi.fn().mockReturnValue([{ id: 1, qty: 2 }]) };
    mockPricer = { calculate: vi.fn().mockReturnValue(99.99) };
    mockInventory = { reserve: vi.fn().mockReturnValue(true) };
    mockPaymentGateway = { charge: vi.fn().mockReturnValue({ ok: true, id: "ch_123" }) };
    mockNotifier = { send: vi.fn() };
    mockAuditLog = { record: vi.fn() };
    mockOrderRepo = { save: vi.fn().mockReturnValue({ id: 42 }) };
    mockMetrics = { increment: vi.fn() };

    service = new CheckoutService(
      mockCart, mockPricer, mockInventory, mockPaymentGateway,
      mockNotifier, mockAuditLog, mockOrderRepo, mockMetrics
    );
  });

  it("processes checkout", () => {
    service.checkout("user-1");

    expect(mockCart.getItems).toHaveBeenCalled();
    expect(mockPricer.calculate).toHaveBeenCalled();
    expect(mockInventory.reserve).toHaveBeenCalled();
    expect(mockPaymentGateway.charge).toHaveBeenCalled();
    expect(mockOrderRepo.save).toHaveBeenCalled();
    expect(mockNotifier.send).toHaveBeenCalled();
    expect(mockAuditLog.record).toHaveBeenCalled();
    expect(mockMetrics.increment).toHaveBeenCalled();
  });
});
