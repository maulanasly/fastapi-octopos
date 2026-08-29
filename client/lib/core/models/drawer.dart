library;


class DrawerSession {
  final int id;
  final int userId;
  final double startingCash;
  final double expectedCash;
  final double? endingCash;
  final String status;
  final String? openedAt;
  final String? closedAt;

  const DrawerSession({
    required this.id,
    required this.userId,
    required this.startingCash,
    required this.expectedCash,
    this.endingCash,
    required this.status,
    this.openedAt,
    this.closedAt,
  });

  factory DrawerSession.fromJson(Map<String, dynamic> json) => DrawerSession(
    id: json['id'] as int,
    userId: json['user_id'] as int,
    startingCash: (json['starting_cash'] as num?)?.toDouble() ?? 0,
    expectedCash: (json['expected_cash'] as num?)?.toDouble() ?? 0,
    endingCash: (json['ending_cash'] as num?)?.toDouble(),
    status: json['status'] as String,
    openedAt: json['opened_at'] as String?,
    closedAt: json['closed_at'] as String?,
  );
}

class ShiftReconciliation {
  final int id;
  final int drawerSessionId;
  final int closedByUserId;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double expectedCash;
  final double countedCash;
  final double cashVariance;
  final double expectedNonCash;
  final double countedNonCash;
  final double nonCashVariance;
  final int completedOrderCount;
  final double grossSalesTotal;
  final double netSalesTotal;

  const ShiftReconciliation({
    required this.id,
    required this.drawerSessionId,
    required this.closedByUserId,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.expectedCash,
    required this.countedCash,
    required this.cashVariance,
    required this.expectedNonCash,
    required this.countedNonCash,
    required this.nonCashVariance,
    required this.completedOrderCount,
    required this.grossSalesTotal,
    required this.netSalesTotal,
  });

  factory ShiftReconciliation.fromJson(Map<String, dynamic> json) =>
      ShiftReconciliation(
        id: json['id'] as int,
        drawerSessionId: json['drawer_session_id'] as int,
        closedByUserId: json['closed_by_user_id'] as int? ?? 0,
        cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
        nonCashSalesTotal:
            (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
        refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
        expectedCash: (json['expected_cash'] as num?)?.toDouble() ?? 0,
        countedCash: (json['counted_cash'] as num?)?.toDouble() ?? 0,
        cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
        expectedNonCash: (json['expected_non_cash'] as num?)?.toDouble() ?? 0,
        countedNonCash: (json['counted_non_cash'] as num?)?.toDouble() ?? 0,
        nonCashVariance: (json['non_cash_variance'] as num?)?.toDouble() ?? 0,
        completedOrderCount: json['completed_order_count'] as int? ?? 0,
        grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
        netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
      );
}

class ShiftReport {
  final int reconciliationId;
  final int drawerSessionId;
  final String? openedAt;
  final String? closedAt;
  final String? operatorName;
  final String? closedByName;
  final double startingCash;
  final double expectedCash;
  final double countedCash;
  final double cashVariance;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double grossSalesTotal;
  final double netSalesTotal;
  final int completedOrderCount;
  final List<PaymentBreakdownItem> paymentBreakdown;

  const ShiftReport({
    required this.reconciliationId,
    required this.drawerSessionId,
    this.openedAt,
    this.closedAt,
    this.operatorName,
    this.closedByName,
    required this.startingCash,
    required this.expectedCash,
    required this.countedCash,
    required this.cashVariance,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.grossSalesTotal,
    required this.netSalesTotal,
    required this.completedOrderCount,
    this.paymentBreakdown = const [],
  });

  factory ShiftReport.fromJson(Map<String, dynamic> json) => ShiftReport(
    reconciliationId: json['reconciliation_id'] as int,
    drawerSessionId: json['drawer_session_id'] as int,
    openedAt: json['opened_at'] as String?,
    closedAt: json['closed_at'] as String?,
    operatorName: json['operator_name'] as String?,
    closedByName: json['closed_by_name'] as String?,
    startingCash: (json['starting_cash'] as num?)?.toDouble() ?? 0,
    expectedCash: (json['expected_cash'] as num?)?.toDouble() ?? 0,
    countedCash: (json['counted_cash'] as num?)?.toDouble() ?? 0,
    cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
    cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
    nonCashSalesTotal: (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
    refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
    grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
    netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
    completedOrderCount: json['completed_order_count'] as int? ?? 0,
    paymentBreakdown: (json['payment_breakdown'] as List? ?? [])
        .map((e) => PaymentBreakdownItem.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class PaymentBreakdownItem {
  final String paymentMethod;
  final int count;
  final double amount;

  const PaymentBreakdownItem({
    required this.paymentMethod,
    required this.count,
    required this.amount,
  });

  factory PaymentBreakdownItem.fromJson(Map<String, dynamic> json) =>
      PaymentBreakdownItem(
        paymentMethod: json['payment_method'] as String,
        count: json['count'] as int? ?? 0,
        amount: (json['amount'] as num?)?.toDouble() ?? 0,
      );
}

class DailyShiftItem {
  final int reconciliationId;
  final int drawerSessionId;
  final String? openedAt;
  final String? closedAt;
  final String? operatorName;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double grossSalesTotal;
  final double netSalesTotal;
  final int completedOrderCount;
  final double cashVariance;

  const DailyShiftItem({
    required this.reconciliationId,
    required this.drawerSessionId,
    this.openedAt,
    this.closedAt,
    this.operatorName,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.grossSalesTotal,
    required this.netSalesTotal,
    required this.completedOrderCount,
    required this.cashVariance,
  });

  factory DailyShiftItem.fromJson(Map<String, dynamic> json) => DailyShiftItem(
    reconciliationId: json['reconciliation_id'] as int,
    drawerSessionId: json['drawer_session_id'] as int,
    openedAt: json['opened_at'] as String?,
    closedAt: json['closed_at'] as String?,
    operatorName: json['operator_name'] as String?,
    cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
    nonCashSalesTotal: (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
    refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
    grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
    netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
    completedOrderCount: json['completed_order_count'] as int? ?? 0,
    cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
  );
}

class DailyCloseTotals {
  final double grossSalesTotal;
  final double netSalesTotal;
  final double cashSalesTotal;
  final double nonCashSalesTotal;
  final double refundsTotal;
  final double cashVariance;
  final double nonCashVariance;
  final int completedOrderCount;
  final int shiftCount;

  const DailyCloseTotals({
    required this.grossSalesTotal,
    required this.netSalesTotal,
    required this.cashSalesTotal,
    required this.nonCashSalesTotal,
    required this.refundsTotal,
    required this.cashVariance,
    required this.nonCashVariance,
    required this.completedOrderCount,
    required this.shiftCount,
  });

  factory DailyCloseTotals.fromJson(Map<String, dynamic> json) =>
      DailyCloseTotals(
        grossSalesTotal: (json['gross_sales_total'] as num?)?.toDouble() ?? 0,
        netSalesTotal: (json['net_sales_total'] as num?)?.toDouble() ?? 0,
        cashSalesTotal: (json['cash_sales_total'] as num?)?.toDouble() ?? 0,
        nonCashSalesTotal:
            (json['non_cash_sales_total'] as num?)?.toDouble() ?? 0,
        refundsTotal: (json['refunds_total'] as num?)?.toDouble() ?? 0,
        cashVariance: (json['cash_variance'] as num?)?.toDouble() ?? 0,
        nonCashVariance: (json['non_cash_variance'] as num?)?.toDouble() ?? 0,
        completedOrderCount: json['completed_order_count'] as int? ?? 0,
        shiftCount: json['shift_count'] as int? ?? 0,
      );
}
