// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $DriftProductsTable extends DriftProducts
    with TableInfo<$DriftProductsTable, DriftProduct> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $DriftProductsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _skuMeta = const VerificationMeta('sku');
  @override
  late final GeneratedColumn<String> sku = GeneratedColumn<String>(
    'sku',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _dataJsonMeta = const VerificationMeta(
    'dataJson',
  );
  @override
  late final GeneratedColumn<String> dataJson = GeneratedColumn<String>(
    'data_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [id, name, sku, dataJson, updatedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'drift_products';
  @override
  VerificationContext validateIntegrity(
    Insertable<DriftProduct> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('sku')) {
      context.handle(
        _skuMeta,
        sku.isAcceptableOrUnknown(data['sku']!, _skuMeta),
      );
    } else if (isInserting) {
      context.missing(_skuMeta);
    }
    if (data.containsKey('data_json')) {
      context.handle(
        _dataJsonMeta,
        dataJson.isAcceptableOrUnknown(data['data_json']!, _dataJsonMeta),
      );
    } else if (isInserting) {
      context.missing(_dataJsonMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  DriftProduct map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return DriftProduct(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      sku: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sku'],
      )!,
      dataJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}data_json'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
    );
  }

  @override
  $DriftProductsTable createAlias(String alias) {
    return $DriftProductsTable(attachedDatabase, alias);
  }
}

class DriftProduct extends DataClass implements Insertable<DriftProduct> {
  final int id;
  final String name;
  final String sku;
  final String dataJson;
  final String updatedAt;
  const DriftProduct({
    required this.id,
    required this.name,
    required this.sku,
    required this.dataJson,
    required this.updatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['name'] = Variable<String>(name);
    map['sku'] = Variable<String>(sku);
    map['data_json'] = Variable<String>(dataJson);
    map['updated_at'] = Variable<String>(updatedAt);
    return map;
  }

  DriftProductsCompanion toCompanion(bool nullToAbsent) {
    return DriftProductsCompanion(
      id: Value(id),
      name: Value(name),
      sku: Value(sku),
      dataJson: Value(dataJson),
      updatedAt: Value(updatedAt),
    );
  }

  factory DriftProduct.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return DriftProduct(
      id: serializer.fromJson<int>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      sku: serializer.fromJson<String>(json['sku']),
      dataJson: serializer.fromJson<String>(json['dataJson']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'name': serializer.toJson<String>(name),
      'sku': serializer.toJson<String>(sku),
      'dataJson': serializer.toJson<String>(dataJson),
      'updatedAt': serializer.toJson<String>(updatedAt),
    };
  }

  DriftProduct copyWith({
    int? id,
    String? name,
    String? sku,
    String? dataJson,
    String? updatedAt,
  }) => DriftProduct(
    id: id ?? this.id,
    name: name ?? this.name,
    sku: sku ?? this.sku,
    dataJson: dataJson ?? this.dataJson,
    updatedAt: updatedAt ?? this.updatedAt,
  );
  DriftProduct copyWithCompanion(DriftProductsCompanion data) {
    return DriftProduct(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      sku: data.sku.present ? data.sku.value : this.sku,
      dataJson: data.dataJson.present ? data.dataJson.value : this.dataJson,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('DriftProduct(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('sku: $sku, ')
          ..write('dataJson: $dataJson, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, name, sku, dataJson, updatedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is DriftProduct &&
          other.id == this.id &&
          other.name == this.name &&
          other.sku == this.sku &&
          other.dataJson == this.dataJson &&
          other.updatedAt == this.updatedAt);
}

class DriftProductsCompanion extends UpdateCompanion<DriftProduct> {
  final Value<int> id;
  final Value<String> name;
  final Value<String> sku;
  final Value<String> dataJson;
  final Value<String> updatedAt;
  const DriftProductsCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.sku = const Value.absent(),
    this.dataJson = const Value.absent(),
    this.updatedAt = const Value.absent(),
  });
  DriftProductsCompanion.insert({
    this.id = const Value.absent(),
    required String name,
    required String sku,
    required String dataJson,
    required String updatedAt,
  }) : name = Value(name),
       sku = Value(sku),
       dataJson = Value(dataJson),
       updatedAt = Value(updatedAt);
  static Insertable<DriftProduct> custom({
    Expression<int>? id,
    Expression<String>? name,
    Expression<String>? sku,
    Expression<String>? dataJson,
    Expression<String>? updatedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (sku != null) 'sku': sku,
      if (dataJson != null) 'data_json': dataJson,
      if (updatedAt != null) 'updated_at': updatedAt,
    });
  }

  DriftProductsCompanion copyWith({
    Value<int>? id,
    Value<String>? name,
    Value<String>? sku,
    Value<String>? dataJson,
    Value<String>? updatedAt,
  }) {
    return DriftProductsCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      sku: sku ?? this.sku,
      dataJson: dataJson ?? this.dataJson,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (sku.present) {
      map['sku'] = Variable<String>(sku.value);
    }
    if (dataJson.present) {
      map['data_json'] = Variable<String>(dataJson.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('DriftProductsCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('sku: $sku, ')
          ..write('dataJson: $dataJson, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }
}

class $DriftCategoriesTable extends DriftCategories
    with TableInfo<$DriftCategoriesTable, DriftCategory> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $DriftCategoriesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _dataJsonMeta = const VerificationMeta(
    'dataJson',
  );
  @override
  late final GeneratedColumn<String> dataJson = GeneratedColumn<String>(
    'data_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [id, name, dataJson, updatedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'drift_categories';
  @override
  VerificationContext validateIntegrity(
    Insertable<DriftCategory> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('data_json')) {
      context.handle(
        _dataJsonMeta,
        dataJson.isAcceptableOrUnknown(data['data_json']!, _dataJsonMeta),
      );
    } else if (isInserting) {
      context.missing(_dataJsonMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  DriftCategory map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return DriftCategory(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      dataJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}data_json'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
    );
  }

  @override
  $DriftCategoriesTable createAlias(String alias) {
    return $DriftCategoriesTable(attachedDatabase, alias);
  }
}

class DriftCategory extends DataClass implements Insertable<DriftCategory> {
  final int id;
  final String name;
  final String dataJson;
  final String updatedAt;
  const DriftCategory({
    required this.id,
    required this.name,
    required this.dataJson,
    required this.updatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['name'] = Variable<String>(name);
    map['data_json'] = Variable<String>(dataJson);
    map['updated_at'] = Variable<String>(updatedAt);
    return map;
  }

  DriftCategoriesCompanion toCompanion(bool nullToAbsent) {
    return DriftCategoriesCompanion(
      id: Value(id),
      name: Value(name),
      dataJson: Value(dataJson),
      updatedAt: Value(updatedAt),
    );
  }

  factory DriftCategory.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return DriftCategory(
      id: serializer.fromJson<int>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      dataJson: serializer.fromJson<String>(json['dataJson']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'name': serializer.toJson<String>(name),
      'dataJson': serializer.toJson<String>(dataJson),
      'updatedAt': serializer.toJson<String>(updatedAt),
    };
  }

  DriftCategory copyWith({
    int? id,
    String? name,
    String? dataJson,
    String? updatedAt,
  }) => DriftCategory(
    id: id ?? this.id,
    name: name ?? this.name,
    dataJson: dataJson ?? this.dataJson,
    updatedAt: updatedAt ?? this.updatedAt,
  );
  DriftCategory copyWithCompanion(DriftCategoriesCompanion data) {
    return DriftCategory(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      dataJson: data.dataJson.present ? data.dataJson.value : this.dataJson,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('DriftCategory(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('dataJson: $dataJson, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, name, dataJson, updatedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is DriftCategory &&
          other.id == this.id &&
          other.name == this.name &&
          other.dataJson == this.dataJson &&
          other.updatedAt == this.updatedAt);
}

class DriftCategoriesCompanion extends UpdateCompanion<DriftCategory> {
  final Value<int> id;
  final Value<String> name;
  final Value<String> dataJson;
  final Value<String> updatedAt;
  const DriftCategoriesCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.dataJson = const Value.absent(),
    this.updatedAt = const Value.absent(),
  });
  DriftCategoriesCompanion.insert({
    this.id = const Value.absent(),
    required String name,
    required String dataJson,
    required String updatedAt,
  }) : name = Value(name),
       dataJson = Value(dataJson),
       updatedAt = Value(updatedAt);
  static Insertable<DriftCategory> custom({
    Expression<int>? id,
    Expression<String>? name,
    Expression<String>? dataJson,
    Expression<String>? updatedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (dataJson != null) 'data_json': dataJson,
      if (updatedAt != null) 'updated_at': updatedAt,
    });
  }

  DriftCategoriesCompanion copyWith({
    Value<int>? id,
    Value<String>? name,
    Value<String>? dataJson,
    Value<String>? updatedAt,
  }) {
    return DriftCategoriesCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      dataJson: dataJson ?? this.dataJson,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (dataJson.present) {
      map['data_json'] = Variable<String>(dataJson.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('DriftCategoriesCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('dataJson: $dataJson, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }
}

class $SyncMetaTable extends SyncMeta
    with TableInfo<$SyncMetaTable, SyncMetaData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncMetaTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
    'key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
    'value',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_meta';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncMetaData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
        _keyMeta,
        key.isAcceptableOrUnknown(data['key']!, _keyMeta),
      );
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
        _valueMeta,
        value.isAcceptableOrUnknown(data['value']!, _valueMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  SyncMetaData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncMetaData(
      key: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}key'],
      )!,
      value: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}value'],
      ),
    );
  }

  @override
  $SyncMetaTable createAlias(String alias) {
    return $SyncMetaTable(attachedDatabase, alias);
  }
}

class SyncMetaData extends DataClass implements Insertable<SyncMetaData> {
  final String key;
  final String? value;
  const SyncMetaData({required this.key, this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    if (!nullToAbsent || value != null) {
      map['value'] = Variable<String>(value);
    }
    return map;
  }

  SyncMetaCompanion toCompanion(bool nullToAbsent) {
    return SyncMetaCompanion(
      key: Value(key),
      value: value == null && nullToAbsent
          ? const Value.absent()
          : Value(value),
    );
  }

  factory SyncMetaData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncMetaData(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String?>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String?>(value),
    };
  }

  SyncMetaData copyWith({
    String? key,
    Value<String?> value = const Value.absent(),
  }) => SyncMetaData(
    key: key ?? this.key,
    value: value.present ? value.value : this.value,
  );
  SyncMetaData copyWithCompanion(SyncMetaCompanion data) {
    return SyncMetaData(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncMetaData(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncMetaData &&
          other.key == this.key &&
          other.value == this.value);
}

class SyncMetaCompanion extends UpdateCompanion<SyncMetaData> {
  final Value<String> key;
  final Value<String?> value;
  final Value<int> rowid;
  const SyncMetaCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SyncMetaCompanion.insert({
    required String key,
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : key = Value(key);
  static Insertable<SyncMetaData> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SyncMetaCompanion copyWith({
    Value<String>? key,
    Value<String?>? value,
    Value<int>? rowid,
  }) {
    return SyncMetaCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncMetaCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $OutboxOrdersTable extends OutboxOrders
    with TableInfo<$OutboxOrdersTable, OutboxOrder> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OutboxOrdersTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _customerIdMeta = const VerificationMeta(
    'customerId',
  );
  @override
  late final GeneratedColumn<int> customerId = GeneratedColumn<int>(
    'customer_id',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _itemsJsonMeta = const VerificationMeta(
    'itemsJson',
  );
  @override
  late final GeneratedColumn<String> itemsJson = GeneratedColumn<String>(
    'items_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _promotionCodeMeta = const VerificationMeta(
    'promotionCode',
  );
  @override
  late final GeneratedColumn<String> promotionCode = GeneratedColumn<String>(
    'promotion_code',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _redeemPointsMeta = const VerificationMeta(
    'redeemPoints',
  );
  @override
  late final GeneratedColumn<int> redeemPoints = GeneratedColumn<int>(
    'redeem_points',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _destinationAddressMeta =
      const VerificationMeta('destinationAddress');
  @override
  late final GeneratedColumn<String> destinationAddress =
      GeneratedColumn<String>(
        'destination_address',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _destinationLatMeta = const VerificationMeta(
    'destinationLat',
  );
  @override
  late final GeneratedColumn<double> destinationLat = GeneratedColumn<double>(
    'destination_lat',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _destinationLngMeta = const VerificationMeta(
    'destinationLng',
  );
  @override
  late final GeneratedColumn<double> destinationLng = GeneratedColumn<double>(
    'destination_lng',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _idempotencyKeyMeta = const VerificationMeta(
    'idempotencyKey',
  );
  @override
  late final GeneratedColumn<String> idempotencyKey = GeneratedColumn<String>(
    'idempotency_key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    $customConstraints: 'UNIQUE NOT NULL',
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('pending'),
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _paymentMethodMeta = const VerificationMeta(
    'paymentMethod',
  );
  @override
  late final GeneratedColumn<String> paymentMethod = GeneratedColumn<String>(
    'payment_method',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _paymentAmountCentsMeta =
      const VerificationMeta('paymentAmountCents');
  @override
  late final GeneratedColumn<int> paymentAmountCents = GeneratedColumn<int>(
    'payment_amount_cents',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _splitJsonMeta = const VerificationMeta(
    'splitJson',
  );
  @override
  late final GeneratedColumn<String> splitJson = GeneratedColumn<String>(
    'split_json',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _payIdempotencyKeyMeta = const VerificationMeta(
    'payIdempotencyKey',
  );
  @override
  late final GeneratedColumn<String> payIdempotencyKey =
      GeneratedColumn<String>(
        'pay_idempotency_key',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    customerId,
    itemsJson,
    promotionCode,
    redeemPoints,
    destinationAddress,
    destinationLat,
    destinationLng,
    idempotencyKey,
    status,
    createdAt,
    lastError,
    paymentMethod,
    paymentAmountCents,
    splitJson,
    payIdempotencyKey,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'outbox_orders';
  @override
  VerificationContext validateIntegrity(
    Insertable<OutboxOrder> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('customer_id')) {
      context.handle(
        _customerIdMeta,
        customerId.isAcceptableOrUnknown(data['customer_id']!, _customerIdMeta),
      );
    }
    if (data.containsKey('items_json')) {
      context.handle(
        _itemsJsonMeta,
        itemsJson.isAcceptableOrUnknown(data['items_json']!, _itemsJsonMeta),
      );
    } else if (isInserting) {
      context.missing(_itemsJsonMeta);
    }
    if (data.containsKey('promotion_code')) {
      context.handle(
        _promotionCodeMeta,
        promotionCode.isAcceptableOrUnknown(
          data['promotion_code']!,
          _promotionCodeMeta,
        ),
      );
    }
    if (data.containsKey('redeem_points')) {
      context.handle(
        _redeemPointsMeta,
        redeemPoints.isAcceptableOrUnknown(
          data['redeem_points']!,
          _redeemPointsMeta,
        ),
      );
    }
    if (data.containsKey('destination_address')) {
      context.handle(
        _destinationAddressMeta,
        destinationAddress.isAcceptableOrUnknown(
          data['destination_address']!,
          _destinationAddressMeta,
        ),
      );
    }
    if (data.containsKey('destination_lat')) {
      context.handle(
        _destinationLatMeta,
        destinationLat.isAcceptableOrUnknown(
          data['destination_lat']!,
          _destinationLatMeta,
        ),
      );
    }
    if (data.containsKey('destination_lng')) {
      context.handle(
        _destinationLngMeta,
        destinationLng.isAcceptableOrUnknown(
          data['destination_lng']!,
          _destinationLngMeta,
        ),
      );
    }
    if (data.containsKey('idempotency_key')) {
      context.handle(
        _idempotencyKeyMeta,
        idempotencyKey.isAcceptableOrUnknown(
          data['idempotency_key']!,
          _idempotencyKeyMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_idempotencyKeyMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    if (data.containsKey('payment_method')) {
      context.handle(
        _paymentMethodMeta,
        paymentMethod.isAcceptableOrUnknown(
          data['payment_method']!,
          _paymentMethodMeta,
        ),
      );
    }
    if (data.containsKey('payment_amount_cents')) {
      context.handle(
        _paymentAmountCentsMeta,
        paymentAmountCents.isAcceptableOrUnknown(
          data['payment_amount_cents']!,
          _paymentAmountCentsMeta,
        ),
      );
    }
    if (data.containsKey('split_json')) {
      context.handle(
        _splitJsonMeta,
        splitJson.isAcceptableOrUnknown(data['split_json']!, _splitJsonMeta),
      );
    }
    if (data.containsKey('pay_idempotency_key')) {
      context.handle(
        _payIdempotencyKeyMeta,
        payIdempotencyKey.isAcceptableOrUnknown(
          data['pay_idempotency_key']!,
          _payIdempotencyKeyMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  OutboxOrder map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OutboxOrder(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      customerId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}customer_id'],
      ),
      itemsJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}items_json'],
      )!,
      promotionCode: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}promotion_code'],
      ),
      redeemPoints: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}redeem_points'],
      )!,
      destinationAddress: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}destination_address'],
      ),
      destinationLat: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}destination_lat'],
      ),
      destinationLng: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}destination_lng'],
      ),
      idempotencyKey: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}idempotency_key'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
      paymentMethod: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}payment_method'],
      ),
      paymentAmountCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}payment_amount_cents'],
      ),
      splitJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}split_json'],
      ),
      payIdempotencyKey: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}pay_idempotency_key'],
      ),
    );
  }

  @override
  $OutboxOrdersTable createAlias(String alias) {
    return $OutboxOrdersTable(attachedDatabase, alias);
  }
}

class OutboxOrder extends DataClass implements Insertable<OutboxOrder> {
  final int id;
  final int? customerId;
  final String itemsJson;
  final String? promotionCode;
  final int redeemPoints;
  final String? destinationAddress;
  final double? destinationLat;
  final double? destinationLng;
  final String idempotencyKey;
  final String status;
  final String createdAt;
  final String? lastError;
  final String? paymentMethod;
  final int? paymentAmountCents;
  final String? splitJson;
  final String? payIdempotencyKey;
  const OutboxOrder({
    required this.id,
    this.customerId,
    required this.itemsJson,
    this.promotionCode,
    required this.redeemPoints,
    this.destinationAddress,
    this.destinationLat,
    this.destinationLng,
    required this.idempotencyKey,
    required this.status,
    required this.createdAt,
    this.lastError,
    this.paymentMethod,
    this.paymentAmountCents,
    this.splitJson,
    this.payIdempotencyKey,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    if (!nullToAbsent || customerId != null) {
      map['customer_id'] = Variable<int>(customerId);
    }
    map['items_json'] = Variable<String>(itemsJson);
    if (!nullToAbsent || promotionCode != null) {
      map['promotion_code'] = Variable<String>(promotionCode);
    }
    map['redeem_points'] = Variable<int>(redeemPoints);
    if (!nullToAbsent || destinationAddress != null) {
      map['destination_address'] = Variable<String>(destinationAddress);
    }
    if (!nullToAbsent || destinationLat != null) {
      map['destination_lat'] = Variable<double>(destinationLat);
    }
    if (!nullToAbsent || destinationLng != null) {
      map['destination_lng'] = Variable<double>(destinationLng);
    }
    map['idempotency_key'] = Variable<String>(idempotencyKey);
    map['status'] = Variable<String>(status);
    map['created_at'] = Variable<String>(createdAt);
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    if (!nullToAbsent || paymentMethod != null) {
      map['payment_method'] = Variable<String>(paymentMethod);
    }
    if (!nullToAbsent || paymentAmountCents != null) {
      map['payment_amount_cents'] = Variable<int>(paymentAmountCents);
    }
    if (!nullToAbsent || splitJson != null) {
      map['split_json'] = Variable<String>(splitJson);
    }
    if (!nullToAbsent || payIdempotencyKey != null) {
      map['pay_idempotency_key'] = Variable<String>(payIdempotencyKey);
    }
    return map;
  }

  OutboxOrdersCompanion toCompanion(bool nullToAbsent) {
    return OutboxOrdersCompanion(
      id: Value(id),
      customerId: customerId == null && nullToAbsent
          ? const Value.absent()
          : Value(customerId),
      itemsJson: Value(itemsJson),
      promotionCode: promotionCode == null && nullToAbsent
          ? const Value.absent()
          : Value(promotionCode),
      redeemPoints: Value(redeemPoints),
      destinationAddress: destinationAddress == null && nullToAbsent
          ? const Value.absent()
          : Value(destinationAddress),
      destinationLat: destinationLat == null && nullToAbsent
          ? const Value.absent()
          : Value(destinationLat),
      destinationLng: destinationLng == null && nullToAbsent
          ? const Value.absent()
          : Value(destinationLng),
      idempotencyKey: Value(idempotencyKey),
      status: Value(status),
      createdAt: Value(createdAt),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
      paymentMethod: paymentMethod == null && nullToAbsent
          ? const Value.absent()
          : Value(paymentMethod),
      paymentAmountCents: paymentAmountCents == null && nullToAbsent
          ? const Value.absent()
          : Value(paymentAmountCents),
      splitJson: splitJson == null && nullToAbsent
          ? const Value.absent()
          : Value(splitJson),
      payIdempotencyKey: payIdempotencyKey == null && nullToAbsent
          ? const Value.absent()
          : Value(payIdempotencyKey),
    );
  }

  factory OutboxOrder.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OutboxOrder(
      id: serializer.fromJson<int>(json['id']),
      customerId: serializer.fromJson<int?>(json['customerId']),
      itemsJson: serializer.fromJson<String>(json['itemsJson']),
      promotionCode: serializer.fromJson<String?>(json['promotionCode']),
      redeemPoints: serializer.fromJson<int>(json['redeemPoints']),
      destinationAddress: serializer.fromJson<String?>(
        json['destinationAddress'],
      ),
      destinationLat: serializer.fromJson<double?>(json['destinationLat']),
      destinationLng: serializer.fromJson<double?>(json['destinationLng']),
      idempotencyKey: serializer.fromJson<String>(json['idempotencyKey']),
      status: serializer.fromJson<String>(json['status']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      lastError: serializer.fromJson<String?>(json['lastError']),
      paymentMethod: serializer.fromJson<String?>(json['paymentMethod']),
      paymentAmountCents: serializer.fromJson<int?>(json['paymentAmountCents']),
      splitJson: serializer.fromJson<String?>(json['splitJson']),
      payIdempotencyKey: serializer.fromJson<String?>(
        json['payIdempotencyKey'],
      ),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'customerId': serializer.toJson<int?>(customerId),
      'itemsJson': serializer.toJson<String>(itemsJson),
      'promotionCode': serializer.toJson<String?>(promotionCode),
      'redeemPoints': serializer.toJson<int>(redeemPoints),
      'destinationAddress': serializer.toJson<String?>(destinationAddress),
      'destinationLat': serializer.toJson<double?>(destinationLat),
      'destinationLng': serializer.toJson<double?>(destinationLng),
      'idempotencyKey': serializer.toJson<String>(idempotencyKey),
      'status': serializer.toJson<String>(status),
      'createdAt': serializer.toJson<String>(createdAt),
      'lastError': serializer.toJson<String?>(lastError),
      'paymentMethod': serializer.toJson<String?>(paymentMethod),
      'paymentAmountCents': serializer.toJson<int?>(paymentAmountCents),
      'splitJson': serializer.toJson<String?>(splitJson),
      'payIdempotencyKey': serializer.toJson<String?>(payIdempotencyKey),
    };
  }

  OutboxOrder copyWith({
    int? id,
    Value<int?> customerId = const Value.absent(),
    String? itemsJson,
    Value<String?> promotionCode = const Value.absent(),
    int? redeemPoints,
    Value<String?> destinationAddress = const Value.absent(),
    Value<double?> destinationLat = const Value.absent(),
    Value<double?> destinationLng = const Value.absent(),
    String? idempotencyKey,
    String? status,
    String? createdAt,
    Value<String?> lastError = const Value.absent(),
    Value<String?> paymentMethod = const Value.absent(),
    Value<int?> paymentAmountCents = const Value.absent(),
    Value<String?> splitJson = const Value.absent(),
    Value<String?> payIdempotencyKey = const Value.absent(),
  }) => OutboxOrder(
    id: id ?? this.id,
    customerId: customerId.present ? customerId.value : this.customerId,
    itemsJson: itemsJson ?? this.itemsJson,
    promotionCode: promotionCode.present
        ? promotionCode.value
        : this.promotionCode,
    redeemPoints: redeemPoints ?? this.redeemPoints,
    destinationAddress: destinationAddress.present
        ? destinationAddress.value
        : this.destinationAddress,
    destinationLat: destinationLat.present
        ? destinationLat.value
        : this.destinationLat,
    destinationLng: destinationLng.present
        ? destinationLng.value
        : this.destinationLng,
    idempotencyKey: idempotencyKey ?? this.idempotencyKey,
    status: status ?? this.status,
    createdAt: createdAt ?? this.createdAt,
    lastError: lastError.present ? lastError.value : this.lastError,
    paymentMethod: paymentMethod.present
        ? paymentMethod.value
        : this.paymentMethod,
    paymentAmountCents: paymentAmountCents.present
        ? paymentAmountCents.value
        : this.paymentAmountCents,
    splitJson: splitJson.present ? splitJson.value : this.splitJson,
    payIdempotencyKey: payIdempotencyKey.present
        ? payIdempotencyKey.value
        : this.payIdempotencyKey,
  );
  OutboxOrder copyWithCompanion(OutboxOrdersCompanion data) {
    return OutboxOrder(
      id: data.id.present ? data.id.value : this.id,
      customerId: data.customerId.present
          ? data.customerId.value
          : this.customerId,
      itemsJson: data.itemsJson.present ? data.itemsJson.value : this.itemsJson,
      promotionCode: data.promotionCode.present
          ? data.promotionCode.value
          : this.promotionCode,
      redeemPoints: data.redeemPoints.present
          ? data.redeemPoints.value
          : this.redeemPoints,
      destinationAddress: data.destinationAddress.present
          ? data.destinationAddress.value
          : this.destinationAddress,
      destinationLat: data.destinationLat.present
          ? data.destinationLat.value
          : this.destinationLat,
      destinationLng: data.destinationLng.present
          ? data.destinationLng.value
          : this.destinationLng,
      idempotencyKey: data.idempotencyKey.present
          ? data.idempotencyKey.value
          : this.idempotencyKey,
      status: data.status.present ? data.status.value : this.status,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
      paymentMethod: data.paymentMethod.present
          ? data.paymentMethod.value
          : this.paymentMethod,
      paymentAmountCents: data.paymentAmountCents.present
          ? data.paymentAmountCents.value
          : this.paymentAmountCents,
      splitJson: data.splitJson.present ? data.splitJson.value : this.splitJson,
      payIdempotencyKey: data.payIdempotencyKey.present
          ? data.payIdempotencyKey.value
          : this.payIdempotencyKey,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OutboxOrder(')
          ..write('id: $id, ')
          ..write('customerId: $customerId, ')
          ..write('itemsJson: $itemsJson, ')
          ..write('promotionCode: $promotionCode, ')
          ..write('redeemPoints: $redeemPoints, ')
          ..write('destinationAddress: $destinationAddress, ')
          ..write('destinationLat: $destinationLat, ')
          ..write('destinationLng: $destinationLng, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('lastError: $lastError, ')
          ..write('paymentMethod: $paymentMethod, ')
          ..write('paymentAmountCents: $paymentAmountCents, ')
          ..write('splitJson: $splitJson, ')
          ..write('payIdempotencyKey: $payIdempotencyKey')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    customerId,
    itemsJson,
    promotionCode,
    redeemPoints,
    destinationAddress,
    destinationLat,
    destinationLng,
    idempotencyKey,
    status,
    createdAt,
    lastError,
    paymentMethod,
    paymentAmountCents,
    splitJson,
    payIdempotencyKey,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OutboxOrder &&
          other.id == this.id &&
          other.customerId == this.customerId &&
          other.itemsJson == this.itemsJson &&
          other.promotionCode == this.promotionCode &&
          other.redeemPoints == this.redeemPoints &&
          other.destinationAddress == this.destinationAddress &&
          other.destinationLat == this.destinationLat &&
          other.destinationLng == this.destinationLng &&
          other.idempotencyKey == this.idempotencyKey &&
          other.status == this.status &&
          other.createdAt == this.createdAt &&
          other.lastError == this.lastError &&
          other.paymentMethod == this.paymentMethod &&
          other.paymentAmountCents == this.paymentAmountCents &&
          other.splitJson == this.splitJson &&
          other.payIdempotencyKey == this.payIdempotencyKey);
}

class OutboxOrdersCompanion extends UpdateCompanion<OutboxOrder> {
  final Value<int> id;
  final Value<int?> customerId;
  final Value<String> itemsJson;
  final Value<String?> promotionCode;
  final Value<int> redeemPoints;
  final Value<String?> destinationAddress;
  final Value<double?> destinationLat;
  final Value<double?> destinationLng;
  final Value<String> idempotencyKey;
  final Value<String> status;
  final Value<String> createdAt;
  final Value<String?> lastError;
  final Value<String?> paymentMethod;
  final Value<int?> paymentAmountCents;
  final Value<String?> splitJson;
  final Value<String?> payIdempotencyKey;
  const OutboxOrdersCompanion({
    this.id = const Value.absent(),
    this.customerId = const Value.absent(),
    this.itemsJson = const Value.absent(),
    this.promotionCode = const Value.absent(),
    this.redeemPoints = const Value.absent(),
    this.destinationAddress = const Value.absent(),
    this.destinationLat = const Value.absent(),
    this.destinationLng = const Value.absent(),
    this.idempotencyKey = const Value.absent(),
    this.status = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.lastError = const Value.absent(),
    this.paymentMethod = const Value.absent(),
    this.paymentAmountCents = const Value.absent(),
    this.splitJson = const Value.absent(),
    this.payIdempotencyKey = const Value.absent(),
  });
  OutboxOrdersCompanion.insert({
    this.id = const Value.absent(),
    this.customerId = const Value.absent(),
    required String itemsJson,
    this.promotionCode = const Value.absent(),
    this.redeemPoints = const Value.absent(),
    this.destinationAddress = const Value.absent(),
    this.destinationLat = const Value.absent(),
    this.destinationLng = const Value.absent(),
    required String idempotencyKey,
    this.status = const Value.absent(),
    required String createdAt,
    this.lastError = const Value.absent(),
    this.paymentMethod = const Value.absent(),
    this.paymentAmountCents = const Value.absent(),
    this.splitJson = const Value.absent(),
    this.payIdempotencyKey = const Value.absent(),
  }) : itemsJson = Value(itemsJson),
       idempotencyKey = Value(idempotencyKey),
       createdAt = Value(createdAt);
  static Insertable<OutboxOrder> custom({
    Expression<int>? id,
    Expression<int>? customerId,
    Expression<String>? itemsJson,
    Expression<String>? promotionCode,
    Expression<int>? redeemPoints,
    Expression<String>? destinationAddress,
    Expression<double>? destinationLat,
    Expression<double>? destinationLng,
    Expression<String>? idempotencyKey,
    Expression<String>? status,
    Expression<String>? createdAt,
    Expression<String>? lastError,
    Expression<String>? paymentMethod,
    Expression<int>? paymentAmountCents,
    Expression<String>? splitJson,
    Expression<String>? payIdempotencyKey,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (customerId != null) 'customer_id': customerId,
      if (itemsJson != null) 'items_json': itemsJson,
      if (promotionCode != null) 'promotion_code': promotionCode,
      if (redeemPoints != null) 'redeem_points': redeemPoints,
      if (destinationAddress != null) 'destination_address': destinationAddress,
      if (destinationLat != null) 'destination_lat': destinationLat,
      if (destinationLng != null) 'destination_lng': destinationLng,
      if (idempotencyKey != null) 'idempotency_key': idempotencyKey,
      if (status != null) 'status': status,
      if (createdAt != null) 'created_at': createdAt,
      if (lastError != null) 'last_error': lastError,
      if (paymentMethod != null) 'payment_method': paymentMethod,
      if (paymentAmountCents != null)
        'payment_amount_cents': paymentAmountCents,
      if (splitJson != null) 'split_json': splitJson,
      if (payIdempotencyKey != null) 'pay_idempotency_key': payIdempotencyKey,
    });
  }

  OutboxOrdersCompanion copyWith({
    Value<int>? id,
    Value<int?>? customerId,
    Value<String>? itemsJson,
    Value<String?>? promotionCode,
    Value<int>? redeemPoints,
    Value<String?>? destinationAddress,
    Value<double?>? destinationLat,
    Value<double?>? destinationLng,
    Value<String>? idempotencyKey,
    Value<String>? status,
    Value<String>? createdAt,
    Value<String?>? lastError,
    Value<String?>? paymentMethod,
    Value<int?>? paymentAmountCents,
    Value<String?>? splitJson,
    Value<String?>? payIdempotencyKey,
  }) {
    return OutboxOrdersCompanion(
      id: id ?? this.id,
      customerId: customerId ?? this.customerId,
      itemsJson: itemsJson ?? this.itemsJson,
      promotionCode: promotionCode ?? this.promotionCode,
      redeemPoints: redeemPoints ?? this.redeemPoints,
      destinationAddress: destinationAddress ?? this.destinationAddress,
      destinationLat: destinationLat ?? this.destinationLat,
      destinationLng: destinationLng ?? this.destinationLng,
      idempotencyKey: idempotencyKey ?? this.idempotencyKey,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      lastError: lastError ?? this.lastError,
      paymentMethod: paymentMethod ?? this.paymentMethod,
      paymentAmountCents: paymentAmountCents ?? this.paymentAmountCents,
      splitJson: splitJson ?? this.splitJson,
      payIdempotencyKey: payIdempotencyKey ?? this.payIdempotencyKey,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (customerId.present) {
      map['customer_id'] = Variable<int>(customerId.value);
    }
    if (itemsJson.present) {
      map['items_json'] = Variable<String>(itemsJson.value);
    }
    if (promotionCode.present) {
      map['promotion_code'] = Variable<String>(promotionCode.value);
    }
    if (redeemPoints.present) {
      map['redeem_points'] = Variable<int>(redeemPoints.value);
    }
    if (destinationAddress.present) {
      map['destination_address'] = Variable<String>(destinationAddress.value);
    }
    if (destinationLat.present) {
      map['destination_lat'] = Variable<double>(destinationLat.value);
    }
    if (destinationLng.present) {
      map['destination_lng'] = Variable<double>(destinationLng.value);
    }
    if (idempotencyKey.present) {
      map['idempotency_key'] = Variable<String>(idempotencyKey.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    if (paymentMethod.present) {
      map['payment_method'] = Variable<String>(paymentMethod.value);
    }
    if (paymentAmountCents.present) {
      map['payment_amount_cents'] = Variable<int>(paymentAmountCents.value);
    }
    if (splitJson.present) {
      map['split_json'] = Variable<String>(splitJson.value);
    }
    if (payIdempotencyKey.present) {
      map['pay_idempotency_key'] = Variable<String>(payIdempotencyKey.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OutboxOrdersCompanion(')
          ..write('id: $id, ')
          ..write('customerId: $customerId, ')
          ..write('itemsJson: $itemsJson, ')
          ..write('promotionCode: $promotionCode, ')
          ..write('redeemPoints: $redeemPoints, ')
          ..write('destinationAddress: $destinationAddress, ')
          ..write('destinationLat: $destinationLat, ')
          ..write('destinationLng: $destinationLng, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('lastError: $lastError, ')
          ..write('paymentMethod: $paymentMethod, ')
          ..write('paymentAmountCents: $paymentAmountCents, ')
          ..write('splitJson: $splitJson, ')
          ..write('payIdempotencyKey: $payIdempotencyKey')
          ..write(')'))
        .toString();
  }
}

class $OutboxPaymentsTable extends OutboxPayments
    with TableInfo<$OutboxPaymentsTable, OutboxPayment> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OutboxPaymentsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _orderIdMeta = const VerificationMeta(
    'orderId',
  );
  @override
  late final GeneratedColumn<int> orderId = GeneratedColumn<int>(
    'order_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _methodMeta = const VerificationMeta('method');
  @override
  late final GeneratedColumn<String> method = GeneratedColumn<String>(
    'method',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _amountCentsMeta = const VerificationMeta(
    'amountCents',
  );
  @override
  late final GeneratedColumn<int> amountCents = GeneratedColumn<int>(
    'amount_cents',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _idempotencyKeyMeta = const VerificationMeta(
    'idempotencyKey',
  );
  @override
  late final GeneratedColumn<String> idempotencyKey = GeneratedColumn<String>(
    'idempotency_key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    $customConstraints: 'UNIQUE NOT NULL',
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('pending'),
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    orderId,
    method,
    amountCents,
    idempotencyKey,
    status,
    createdAt,
    lastError,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'outbox_payments';
  @override
  VerificationContext validateIntegrity(
    Insertable<OutboxPayment> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('order_id')) {
      context.handle(
        _orderIdMeta,
        orderId.isAcceptableOrUnknown(data['order_id']!, _orderIdMeta),
      );
    } else if (isInserting) {
      context.missing(_orderIdMeta);
    }
    if (data.containsKey('method')) {
      context.handle(
        _methodMeta,
        method.isAcceptableOrUnknown(data['method']!, _methodMeta),
      );
    } else if (isInserting) {
      context.missing(_methodMeta);
    }
    if (data.containsKey('amount_cents')) {
      context.handle(
        _amountCentsMeta,
        amountCents.isAcceptableOrUnknown(
          data['amount_cents']!,
          _amountCentsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_amountCentsMeta);
    }
    if (data.containsKey('idempotency_key')) {
      context.handle(
        _idempotencyKeyMeta,
        idempotencyKey.isAcceptableOrUnknown(
          data['idempotency_key']!,
          _idempotencyKeyMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_idempotencyKeyMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  OutboxPayment map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OutboxPayment(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      orderId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}order_id'],
      )!,
      method: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}method'],
      )!,
      amountCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}amount_cents'],
      )!,
      idempotencyKey: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}idempotency_key'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
    );
  }

  @override
  $OutboxPaymentsTable createAlias(String alias) {
    return $OutboxPaymentsTable(attachedDatabase, alias);
  }
}

class OutboxPayment extends DataClass implements Insertable<OutboxPayment> {
  final int id;
  final int orderId;
  final String method;
  final int amountCents;
  final String idempotencyKey;
  final String status;
  final String createdAt;
  final String? lastError;
  const OutboxPayment({
    required this.id,
    required this.orderId,
    required this.method,
    required this.amountCents,
    required this.idempotencyKey,
    required this.status,
    required this.createdAt,
    this.lastError,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['order_id'] = Variable<int>(orderId);
    map['method'] = Variable<String>(method);
    map['amount_cents'] = Variable<int>(amountCents);
    map['idempotency_key'] = Variable<String>(idempotencyKey);
    map['status'] = Variable<String>(status);
    map['created_at'] = Variable<String>(createdAt);
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    return map;
  }

  OutboxPaymentsCompanion toCompanion(bool nullToAbsent) {
    return OutboxPaymentsCompanion(
      id: Value(id),
      orderId: Value(orderId),
      method: Value(method),
      amountCents: Value(amountCents),
      idempotencyKey: Value(idempotencyKey),
      status: Value(status),
      createdAt: Value(createdAt),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
    );
  }

  factory OutboxPayment.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OutboxPayment(
      id: serializer.fromJson<int>(json['id']),
      orderId: serializer.fromJson<int>(json['orderId']),
      method: serializer.fromJson<String>(json['method']),
      amountCents: serializer.fromJson<int>(json['amountCents']),
      idempotencyKey: serializer.fromJson<String>(json['idempotencyKey']),
      status: serializer.fromJson<String>(json['status']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      lastError: serializer.fromJson<String?>(json['lastError']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'orderId': serializer.toJson<int>(orderId),
      'method': serializer.toJson<String>(method),
      'amountCents': serializer.toJson<int>(amountCents),
      'idempotencyKey': serializer.toJson<String>(idempotencyKey),
      'status': serializer.toJson<String>(status),
      'createdAt': serializer.toJson<String>(createdAt),
      'lastError': serializer.toJson<String?>(lastError),
    };
  }

  OutboxPayment copyWith({
    int? id,
    int? orderId,
    String? method,
    int? amountCents,
    String? idempotencyKey,
    String? status,
    String? createdAt,
    Value<String?> lastError = const Value.absent(),
  }) => OutboxPayment(
    id: id ?? this.id,
    orderId: orderId ?? this.orderId,
    method: method ?? this.method,
    amountCents: amountCents ?? this.amountCents,
    idempotencyKey: idempotencyKey ?? this.idempotencyKey,
    status: status ?? this.status,
    createdAt: createdAt ?? this.createdAt,
    lastError: lastError.present ? lastError.value : this.lastError,
  );
  OutboxPayment copyWithCompanion(OutboxPaymentsCompanion data) {
    return OutboxPayment(
      id: data.id.present ? data.id.value : this.id,
      orderId: data.orderId.present ? data.orderId.value : this.orderId,
      method: data.method.present ? data.method.value : this.method,
      amountCents: data.amountCents.present
          ? data.amountCents.value
          : this.amountCents,
      idempotencyKey: data.idempotencyKey.present
          ? data.idempotencyKey.value
          : this.idempotencyKey,
      status: data.status.present ? data.status.value : this.status,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OutboxPayment(')
          ..write('id: $id, ')
          ..write('orderId: $orderId, ')
          ..write('method: $method, ')
          ..write('amountCents: $amountCents, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    orderId,
    method,
    amountCents,
    idempotencyKey,
    status,
    createdAt,
    lastError,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OutboxPayment &&
          other.id == this.id &&
          other.orderId == this.orderId &&
          other.method == this.method &&
          other.amountCents == this.amountCents &&
          other.idempotencyKey == this.idempotencyKey &&
          other.status == this.status &&
          other.createdAt == this.createdAt &&
          other.lastError == this.lastError);
}

class OutboxPaymentsCompanion extends UpdateCompanion<OutboxPayment> {
  final Value<int> id;
  final Value<int> orderId;
  final Value<String> method;
  final Value<int> amountCents;
  final Value<String> idempotencyKey;
  final Value<String> status;
  final Value<String> createdAt;
  final Value<String?> lastError;
  const OutboxPaymentsCompanion({
    this.id = const Value.absent(),
    this.orderId = const Value.absent(),
    this.method = const Value.absent(),
    this.amountCents = const Value.absent(),
    this.idempotencyKey = const Value.absent(),
    this.status = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.lastError = const Value.absent(),
  });
  OutboxPaymentsCompanion.insert({
    this.id = const Value.absent(),
    required int orderId,
    required String method,
    required int amountCents,
    required String idempotencyKey,
    this.status = const Value.absent(),
    required String createdAt,
    this.lastError = const Value.absent(),
  }) : orderId = Value(orderId),
       method = Value(method),
       amountCents = Value(amountCents),
       idempotencyKey = Value(idempotencyKey),
       createdAt = Value(createdAt);
  static Insertable<OutboxPayment> custom({
    Expression<int>? id,
    Expression<int>? orderId,
    Expression<String>? method,
    Expression<int>? amountCents,
    Expression<String>? idempotencyKey,
    Expression<String>? status,
    Expression<String>? createdAt,
    Expression<String>? lastError,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (orderId != null) 'order_id': orderId,
      if (method != null) 'method': method,
      if (amountCents != null) 'amount_cents': amountCents,
      if (idempotencyKey != null) 'idempotency_key': idempotencyKey,
      if (status != null) 'status': status,
      if (createdAt != null) 'created_at': createdAt,
      if (lastError != null) 'last_error': lastError,
    });
  }

  OutboxPaymentsCompanion copyWith({
    Value<int>? id,
    Value<int>? orderId,
    Value<String>? method,
    Value<int>? amountCents,
    Value<String>? idempotencyKey,
    Value<String>? status,
    Value<String>? createdAt,
    Value<String?>? lastError,
  }) {
    return OutboxPaymentsCompanion(
      id: id ?? this.id,
      orderId: orderId ?? this.orderId,
      method: method ?? this.method,
      amountCents: amountCents ?? this.amountCents,
      idempotencyKey: idempotencyKey ?? this.idempotencyKey,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      lastError: lastError ?? this.lastError,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (orderId.present) {
      map['order_id'] = Variable<int>(orderId.value);
    }
    if (method.present) {
      map['method'] = Variable<String>(method.value);
    }
    if (amountCents.present) {
      map['amount_cents'] = Variable<int>(amountCents.value);
    }
    if (idempotencyKey.present) {
      map['idempotency_key'] = Variable<String>(idempotencyKey.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OutboxPaymentsCompanion(')
          ..write('id: $id, ')
          ..write('orderId: $orderId, ')
          ..write('method: $method, ')
          ..write('amountCents: $amountCents, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }
}

class $OutboxEventsTable extends OutboxEvents
    with TableInfo<$OutboxEventsTable, OutboxEvent> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OutboxEventsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _eventTypeMeta = const VerificationMeta(
    'eventType',
  );
  @override
  late final GeneratedColumn<String> eventType = GeneratedColumn<String>(
    'event_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _clientEventIdMeta = const VerificationMeta(
    'clientEventId',
  );
  @override
  late final GeneratedColumn<String> clientEventId = GeneratedColumn<String>(
    'client_event_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    $customConstraints: 'UNIQUE NOT NULL',
  );
  static const VerificationMeta _payloadJsonMeta = const VerificationMeta(
    'payloadJson',
  );
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
    'payload_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _idempotencyKeyMeta = const VerificationMeta(
    'idempotencyKey',
  );
  @override
  late final GeneratedColumn<String> idempotencyKey = GeneratedColumn<String>(
    'idempotency_key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('pending'),
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    eventType,
    clientEventId,
    payloadJson,
    idempotencyKey,
    status,
    createdAt,
    lastError,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'outbox_events';
  @override
  VerificationContext validateIntegrity(
    Insertable<OutboxEvent> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('event_type')) {
      context.handle(
        _eventTypeMeta,
        eventType.isAcceptableOrUnknown(data['event_type']!, _eventTypeMeta),
      );
    } else if (isInserting) {
      context.missing(_eventTypeMeta);
    }
    if (data.containsKey('client_event_id')) {
      context.handle(
        _clientEventIdMeta,
        clientEventId.isAcceptableOrUnknown(
          data['client_event_id']!,
          _clientEventIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_clientEventIdMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
        _payloadJsonMeta,
        payloadJson.isAcceptableOrUnknown(
          data['payload_json']!,
          _payloadJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('idempotency_key')) {
      context.handle(
        _idempotencyKeyMeta,
        idempotencyKey.isAcceptableOrUnknown(
          data['idempotency_key']!,
          _idempotencyKeyMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_idempotencyKeyMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  OutboxEvent map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OutboxEvent(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      eventType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}event_type'],
      )!,
      clientEventId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}client_event_id'],
      )!,
      payloadJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}payload_json'],
      )!,
      idempotencyKey: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}idempotency_key'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
    );
  }

  @override
  $OutboxEventsTable createAlias(String alias) {
    return $OutboxEventsTable(attachedDatabase, alias);
  }
}

class OutboxEvent extends DataClass implements Insertable<OutboxEvent> {
  final int id;
  final String eventType;
  final String clientEventId;
  final String payloadJson;
  final String idempotencyKey;
  final String status;
  final String createdAt;
  final String? lastError;
  const OutboxEvent({
    required this.id,
    required this.eventType,
    required this.clientEventId,
    required this.payloadJson,
    required this.idempotencyKey,
    required this.status,
    required this.createdAt,
    this.lastError,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['event_type'] = Variable<String>(eventType);
    map['client_event_id'] = Variable<String>(clientEventId);
    map['payload_json'] = Variable<String>(payloadJson);
    map['idempotency_key'] = Variable<String>(idempotencyKey);
    map['status'] = Variable<String>(status);
    map['created_at'] = Variable<String>(createdAt);
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    return map;
  }

  OutboxEventsCompanion toCompanion(bool nullToAbsent) {
    return OutboxEventsCompanion(
      id: Value(id),
      eventType: Value(eventType),
      clientEventId: Value(clientEventId),
      payloadJson: Value(payloadJson),
      idempotencyKey: Value(idempotencyKey),
      status: Value(status),
      createdAt: Value(createdAt),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
    );
  }

  factory OutboxEvent.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OutboxEvent(
      id: serializer.fromJson<int>(json['id']),
      eventType: serializer.fromJson<String>(json['eventType']),
      clientEventId: serializer.fromJson<String>(json['clientEventId']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      idempotencyKey: serializer.fromJson<String>(json['idempotencyKey']),
      status: serializer.fromJson<String>(json['status']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      lastError: serializer.fromJson<String?>(json['lastError']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'eventType': serializer.toJson<String>(eventType),
      'clientEventId': serializer.toJson<String>(clientEventId),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'idempotencyKey': serializer.toJson<String>(idempotencyKey),
      'status': serializer.toJson<String>(status),
      'createdAt': serializer.toJson<String>(createdAt),
      'lastError': serializer.toJson<String?>(lastError),
    };
  }

  OutboxEvent copyWith({
    int? id,
    String? eventType,
    String? clientEventId,
    String? payloadJson,
    String? idempotencyKey,
    String? status,
    String? createdAt,
    Value<String?> lastError = const Value.absent(),
  }) => OutboxEvent(
    id: id ?? this.id,
    eventType: eventType ?? this.eventType,
    clientEventId: clientEventId ?? this.clientEventId,
    payloadJson: payloadJson ?? this.payloadJson,
    idempotencyKey: idempotencyKey ?? this.idempotencyKey,
    status: status ?? this.status,
    createdAt: createdAt ?? this.createdAt,
    lastError: lastError.present ? lastError.value : this.lastError,
  );
  OutboxEvent copyWithCompanion(OutboxEventsCompanion data) {
    return OutboxEvent(
      id: data.id.present ? data.id.value : this.id,
      eventType: data.eventType.present ? data.eventType.value : this.eventType,
      clientEventId: data.clientEventId.present
          ? data.clientEventId.value
          : this.clientEventId,
      payloadJson: data.payloadJson.present
          ? data.payloadJson.value
          : this.payloadJson,
      idempotencyKey: data.idempotencyKey.present
          ? data.idempotencyKey.value
          : this.idempotencyKey,
      status: data.status.present ? data.status.value : this.status,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OutboxEvent(')
          ..write('id: $id, ')
          ..write('eventType: $eventType, ')
          ..write('clientEventId: $clientEventId, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    eventType,
    clientEventId,
    payloadJson,
    idempotencyKey,
    status,
    createdAt,
    lastError,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OutboxEvent &&
          other.id == this.id &&
          other.eventType == this.eventType &&
          other.clientEventId == this.clientEventId &&
          other.payloadJson == this.payloadJson &&
          other.idempotencyKey == this.idempotencyKey &&
          other.status == this.status &&
          other.createdAt == this.createdAt &&
          other.lastError == this.lastError);
}

class OutboxEventsCompanion extends UpdateCompanion<OutboxEvent> {
  final Value<int> id;
  final Value<String> eventType;
  final Value<String> clientEventId;
  final Value<String> payloadJson;
  final Value<String> idempotencyKey;
  final Value<String> status;
  final Value<String> createdAt;
  final Value<String?> lastError;
  const OutboxEventsCompanion({
    this.id = const Value.absent(),
    this.eventType = const Value.absent(),
    this.clientEventId = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.idempotencyKey = const Value.absent(),
    this.status = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.lastError = const Value.absent(),
  });
  OutboxEventsCompanion.insert({
    this.id = const Value.absent(),
    required String eventType,
    required String clientEventId,
    required String payloadJson,
    required String idempotencyKey,
    this.status = const Value.absent(),
    required String createdAt,
    this.lastError = const Value.absent(),
  }) : eventType = Value(eventType),
       clientEventId = Value(clientEventId),
       payloadJson = Value(payloadJson),
       idempotencyKey = Value(idempotencyKey),
       createdAt = Value(createdAt);
  static Insertable<OutboxEvent> custom({
    Expression<int>? id,
    Expression<String>? eventType,
    Expression<String>? clientEventId,
    Expression<String>? payloadJson,
    Expression<String>? idempotencyKey,
    Expression<String>? status,
    Expression<String>? createdAt,
    Expression<String>? lastError,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (eventType != null) 'event_type': eventType,
      if (clientEventId != null) 'client_event_id': clientEventId,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (idempotencyKey != null) 'idempotency_key': idempotencyKey,
      if (status != null) 'status': status,
      if (createdAt != null) 'created_at': createdAt,
      if (lastError != null) 'last_error': lastError,
    });
  }

  OutboxEventsCompanion copyWith({
    Value<int>? id,
    Value<String>? eventType,
    Value<String>? clientEventId,
    Value<String>? payloadJson,
    Value<String>? idempotencyKey,
    Value<String>? status,
    Value<String>? createdAt,
    Value<String?>? lastError,
  }) {
    return OutboxEventsCompanion(
      id: id ?? this.id,
      eventType: eventType ?? this.eventType,
      clientEventId: clientEventId ?? this.clientEventId,
      payloadJson: payloadJson ?? this.payloadJson,
      idempotencyKey: idempotencyKey ?? this.idempotencyKey,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      lastError: lastError ?? this.lastError,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (eventType.present) {
      map['event_type'] = Variable<String>(eventType.value);
    }
    if (clientEventId.present) {
      map['client_event_id'] = Variable<String>(clientEventId.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (idempotencyKey.present) {
      map['idempotency_key'] = Variable<String>(idempotencyKey.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OutboxEventsCompanion(')
          ..write('id: $id, ')
          ..write('eventType: $eventType, ')
          ..write('clientEventId: $clientEventId, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $DriftProductsTable driftProducts = $DriftProductsTable(this);
  late final $DriftCategoriesTable driftCategories = $DriftCategoriesTable(
    this,
  );
  late final $SyncMetaTable syncMeta = $SyncMetaTable(this);
  late final $OutboxOrdersTable outboxOrders = $OutboxOrdersTable(this);
  late final $OutboxPaymentsTable outboxPayments = $OutboxPaymentsTable(this);
  late final $OutboxEventsTable outboxEvents = $OutboxEventsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    driftProducts,
    driftCategories,
    syncMeta,
    outboxOrders,
    outboxPayments,
    outboxEvents,
  ];
}

typedef $$DriftProductsTableCreateCompanionBuilder =
    DriftProductsCompanion Function({
      Value<int> id,
      required String name,
      required String sku,
      required String dataJson,
      required String updatedAt,
    });
typedef $$DriftProductsTableUpdateCompanionBuilder =
    DriftProductsCompanion Function({
      Value<int> id,
      Value<String> name,
      Value<String> sku,
      Value<String> dataJson,
      Value<String> updatedAt,
    });

class $$DriftProductsTableFilterComposer
    extends Composer<_$AppDatabase, $DriftProductsTable> {
  $$DriftProductsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sku => $composableBuilder(
    column: $table.sku,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get dataJson => $composableBuilder(
    column: $table.dataJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$DriftProductsTableOrderingComposer
    extends Composer<_$AppDatabase, $DriftProductsTable> {
  $$DriftProductsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sku => $composableBuilder(
    column: $table.sku,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get dataJson => $composableBuilder(
    column: $table.dataJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$DriftProductsTableAnnotationComposer
    extends Composer<_$AppDatabase, $DriftProductsTable> {
  $$DriftProductsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get sku =>
      $composableBuilder(column: $table.sku, builder: (column) => column);

  GeneratedColumn<String> get dataJson =>
      $composableBuilder(column: $table.dataJson, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);
}

class $$DriftProductsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $DriftProductsTable,
          DriftProduct,
          $$DriftProductsTableFilterComposer,
          $$DriftProductsTableOrderingComposer,
          $$DriftProductsTableAnnotationComposer,
          $$DriftProductsTableCreateCompanionBuilder,
          $$DriftProductsTableUpdateCompanionBuilder,
          (
            DriftProduct,
            BaseReferences<_$AppDatabase, $DriftProductsTable, DriftProduct>,
          ),
          DriftProduct,
          PrefetchHooks Function()
        > {
  $$DriftProductsTableTableManager(_$AppDatabase db, $DriftProductsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$DriftProductsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$DriftProductsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$DriftProductsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<String> sku = const Value.absent(),
                Value<String> dataJson = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
              }) => DriftProductsCompanion(
                id: id,
                name: name,
                sku: sku,
                dataJson: dataJson,
                updatedAt: updatedAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String name,
                required String sku,
                required String dataJson,
                required String updatedAt,
              }) => DriftProductsCompanion.insert(
                id: id,
                name: name,
                sku: sku,
                dataJson: dataJson,
                updatedAt: updatedAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$DriftProductsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $DriftProductsTable,
      DriftProduct,
      $$DriftProductsTableFilterComposer,
      $$DriftProductsTableOrderingComposer,
      $$DriftProductsTableAnnotationComposer,
      $$DriftProductsTableCreateCompanionBuilder,
      $$DriftProductsTableUpdateCompanionBuilder,
      (
        DriftProduct,
        BaseReferences<_$AppDatabase, $DriftProductsTable, DriftProduct>,
      ),
      DriftProduct,
      PrefetchHooks Function()
    >;
typedef $$DriftCategoriesTableCreateCompanionBuilder =
    DriftCategoriesCompanion Function({
      Value<int> id,
      required String name,
      required String dataJson,
      required String updatedAt,
    });
typedef $$DriftCategoriesTableUpdateCompanionBuilder =
    DriftCategoriesCompanion Function({
      Value<int> id,
      Value<String> name,
      Value<String> dataJson,
      Value<String> updatedAt,
    });

class $$DriftCategoriesTableFilterComposer
    extends Composer<_$AppDatabase, $DriftCategoriesTable> {
  $$DriftCategoriesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get dataJson => $composableBuilder(
    column: $table.dataJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$DriftCategoriesTableOrderingComposer
    extends Composer<_$AppDatabase, $DriftCategoriesTable> {
  $$DriftCategoriesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get dataJson => $composableBuilder(
    column: $table.dataJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$DriftCategoriesTableAnnotationComposer
    extends Composer<_$AppDatabase, $DriftCategoriesTable> {
  $$DriftCategoriesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get dataJson =>
      $composableBuilder(column: $table.dataJson, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);
}

class $$DriftCategoriesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $DriftCategoriesTable,
          DriftCategory,
          $$DriftCategoriesTableFilterComposer,
          $$DriftCategoriesTableOrderingComposer,
          $$DriftCategoriesTableAnnotationComposer,
          $$DriftCategoriesTableCreateCompanionBuilder,
          $$DriftCategoriesTableUpdateCompanionBuilder,
          (
            DriftCategory,
            BaseReferences<_$AppDatabase, $DriftCategoriesTable, DriftCategory>,
          ),
          DriftCategory,
          PrefetchHooks Function()
        > {
  $$DriftCategoriesTableTableManager(
    _$AppDatabase db,
    $DriftCategoriesTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$DriftCategoriesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$DriftCategoriesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$DriftCategoriesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<String> dataJson = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
              }) => DriftCategoriesCompanion(
                id: id,
                name: name,
                dataJson: dataJson,
                updatedAt: updatedAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String name,
                required String dataJson,
                required String updatedAt,
              }) => DriftCategoriesCompanion.insert(
                id: id,
                name: name,
                dataJson: dataJson,
                updatedAt: updatedAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$DriftCategoriesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $DriftCategoriesTable,
      DriftCategory,
      $$DriftCategoriesTableFilterComposer,
      $$DriftCategoriesTableOrderingComposer,
      $$DriftCategoriesTableAnnotationComposer,
      $$DriftCategoriesTableCreateCompanionBuilder,
      $$DriftCategoriesTableUpdateCompanionBuilder,
      (
        DriftCategory,
        BaseReferences<_$AppDatabase, $DriftCategoriesTable, DriftCategory>,
      ),
      DriftCategory,
      PrefetchHooks Function()
    >;
typedef $$SyncMetaTableCreateCompanionBuilder =
    SyncMetaCompanion Function({
      required String key,
      Value<String?> value,
      Value<int> rowid,
    });
typedef $$SyncMetaTableUpdateCompanionBuilder =
    SyncMetaCompanion Function({
      Value<String> key,
      Value<String?> value,
      Value<int> rowid,
    });

class $$SyncMetaTableFilterComposer
    extends Composer<_$AppDatabase, $SyncMetaTable> {
  $$SyncMetaTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncMetaTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncMetaTable> {
  $$SyncMetaTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncMetaTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncMetaTable> {
  $$SyncMetaTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$SyncMetaTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncMetaTable,
          SyncMetaData,
          $$SyncMetaTableFilterComposer,
          $$SyncMetaTableOrderingComposer,
          $$SyncMetaTableAnnotationComposer,
          $$SyncMetaTableCreateCompanionBuilder,
          $$SyncMetaTableUpdateCompanionBuilder,
          (
            SyncMetaData,
            BaseReferences<_$AppDatabase, $SyncMetaTable, SyncMetaData>,
          ),
          SyncMetaData,
          PrefetchHooks Function()
        > {
  $$SyncMetaTableTableManager(_$AppDatabase db, $SyncMetaTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncMetaTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncMetaTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncMetaTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> key = const Value.absent(),
                Value<String?> value = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncMetaCompanion(key: key, value: value, rowid: rowid),
          createCompanionCallback:
              ({
                required String key,
                Value<String?> value = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncMetaCompanion.insert(
                key: key,
                value: value,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncMetaTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncMetaTable,
      SyncMetaData,
      $$SyncMetaTableFilterComposer,
      $$SyncMetaTableOrderingComposer,
      $$SyncMetaTableAnnotationComposer,
      $$SyncMetaTableCreateCompanionBuilder,
      $$SyncMetaTableUpdateCompanionBuilder,
      (
        SyncMetaData,
        BaseReferences<_$AppDatabase, $SyncMetaTable, SyncMetaData>,
      ),
      SyncMetaData,
      PrefetchHooks Function()
    >;
typedef $$OutboxOrdersTableCreateCompanionBuilder =
    OutboxOrdersCompanion Function({
      Value<int> id,
      Value<int?> customerId,
      required String itemsJson,
      Value<String?> promotionCode,
      Value<int> redeemPoints,
      Value<String?> destinationAddress,
      Value<double?> destinationLat,
      Value<double?> destinationLng,
      required String idempotencyKey,
      Value<String> status,
      required String createdAt,
      Value<String?> lastError,
      Value<String?> paymentMethod,
      Value<int?> paymentAmountCents,
      Value<String?> splitJson,
      Value<String?> payIdempotencyKey,
    });
typedef $$OutboxOrdersTableUpdateCompanionBuilder =
    OutboxOrdersCompanion Function({
      Value<int> id,
      Value<int?> customerId,
      Value<String> itemsJson,
      Value<String?> promotionCode,
      Value<int> redeemPoints,
      Value<String?> destinationAddress,
      Value<double?> destinationLat,
      Value<double?> destinationLng,
      Value<String> idempotencyKey,
      Value<String> status,
      Value<String> createdAt,
      Value<String?> lastError,
      Value<String?> paymentMethod,
      Value<int?> paymentAmountCents,
      Value<String?> splitJson,
      Value<String?> payIdempotencyKey,
    });

class $$OutboxOrdersTableFilterComposer
    extends Composer<_$AppDatabase, $OutboxOrdersTable> {
  $$OutboxOrdersTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get customerId => $composableBuilder(
    column: $table.customerId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get itemsJson => $composableBuilder(
    column: $table.itemsJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get promotionCode => $composableBuilder(
    column: $table.promotionCode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get redeemPoints => $composableBuilder(
    column: $table.redeemPoints,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get destinationAddress => $composableBuilder(
    column: $table.destinationAddress,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get destinationLat => $composableBuilder(
    column: $table.destinationLat,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get destinationLng => $composableBuilder(
    column: $table.destinationLng,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get paymentMethod => $composableBuilder(
    column: $table.paymentMethod,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get paymentAmountCents => $composableBuilder(
    column: $table.paymentAmountCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get splitJson => $composableBuilder(
    column: $table.splitJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get payIdempotencyKey => $composableBuilder(
    column: $table.payIdempotencyKey,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OutboxOrdersTableOrderingComposer
    extends Composer<_$AppDatabase, $OutboxOrdersTable> {
  $$OutboxOrdersTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get customerId => $composableBuilder(
    column: $table.customerId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get itemsJson => $composableBuilder(
    column: $table.itemsJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get promotionCode => $composableBuilder(
    column: $table.promotionCode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get redeemPoints => $composableBuilder(
    column: $table.redeemPoints,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get destinationAddress => $composableBuilder(
    column: $table.destinationAddress,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get destinationLat => $composableBuilder(
    column: $table.destinationLat,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get destinationLng => $composableBuilder(
    column: $table.destinationLng,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get paymentMethod => $composableBuilder(
    column: $table.paymentMethod,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get paymentAmountCents => $composableBuilder(
    column: $table.paymentAmountCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get splitJson => $composableBuilder(
    column: $table.splitJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get payIdempotencyKey => $composableBuilder(
    column: $table.payIdempotencyKey,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OutboxOrdersTableAnnotationComposer
    extends Composer<_$AppDatabase, $OutboxOrdersTable> {
  $$OutboxOrdersTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<int> get customerId => $composableBuilder(
    column: $table.customerId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get itemsJson =>
      $composableBuilder(column: $table.itemsJson, builder: (column) => column);

  GeneratedColumn<String> get promotionCode => $composableBuilder(
    column: $table.promotionCode,
    builder: (column) => column,
  );

  GeneratedColumn<int> get redeemPoints => $composableBuilder(
    column: $table.redeemPoints,
    builder: (column) => column,
  );

  GeneratedColumn<String> get destinationAddress => $composableBuilder(
    column: $table.destinationAddress,
    builder: (column) => column,
  );

  GeneratedColumn<double> get destinationLat => $composableBuilder(
    column: $table.destinationLat,
    builder: (column) => column,
  );

  GeneratedColumn<double> get destinationLng => $composableBuilder(
    column: $table.destinationLng,
    builder: (column) => column,
  );

  GeneratedColumn<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => column,
  );

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);

  GeneratedColumn<String> get paymentMethod => $composableBuilder(
    column: $table.paymentMethod,
    builder: (column) => column,
  );

  GeneratedColumn<int> get paymentAmountCents => $composableBuilder(
    column: $table.paymentAmountCents,
    builder: (column) => column,
  );

  GeneratedColumn<String> get splitJson =>
      $composableBuilder(column: $table.splitJson, builder: (column) => column);

  GeneratedColumn<String> get payIdempotencyKey => $composableBuilder(
    column: $table.payIdempotencyKey,
    builder: (column) => column,
  );
}

class $$OutboxOrdersTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OutboxOrdersTable,
          OutboxOrder,
          $$OutboxOrdersTableFilterComposer,
          $$OutboxOrdersTableOrderingComposer,
          $$OutboxOrdersTableAnnotationComposer,
          $$OutboxOrdersTableCreateCompanionBuilder,
          $$OutboxOrdersTableUpdateCompanionBuilder,
          (
            OutboxOrder,
            BaseReferences<_$AppDatabase, $OutboxOrdersTable, OutboxOrder>,
          ),
          OutboxOrder,
          PrefetchHooks Function()
        > {
  $$OutboxOrdersTableTableManager(_$AppDatabase db, $OutboxOrdersTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OutboxOrdersTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OutboxOrdersTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OutboxOrdersTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int?> customerId = const Value.absent(),
                Value<String> itemsJson = const Value.absent(),
                Value<String?> promotionCode = const Value.absent(),
                Value<int> redeemPoints = const Value.absent(),
                Value<String?> destinationAddress = const Value.absent(),
                Value<double?> destinationLat = const Value.absent(),
                Value<double?> destinationLng = const Value.absent(),
                Value<String> idempotencyKey = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<String?> paymentMethod = const Value.absent(),
                Value<int?> paymentAmountCents = const Value.absent(),
                Value<String?> splitJson = const Value.absent(),
                Value<String?> payIdempotencyKey = const Value.absent(),
              }) => OutboxOrdersCompanion(
                id: id,
                customerId: customerId,
                itemsJson: itemsJson,
                promotionCode: promotionCode,
                redeemPoints: redeemPoints,
                destinationAddress: destinationAddress,
                destinationLat: destinationLat,
                destinationLng: destinationLng,
                idempotencyKey: idempotencyKey,
                status: status,
                createdAt: createdAt,
                lastError: lastError,
                paymentMethod: paymentMethod,
                paymentAmountCents: paymentAmountCents,
                splitJson: splitJson,
                payIdempotencyKey: payIdempotencyKey,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int?> customerId = const Value.absent(),
                required String itemsJson,
                Value<String?> promotionCode = const Value.absent(),
                Value<int> redeemPoints = const Value.absent(),
                Value<String?> destinationAddress = const Value.absent(),
                Value<double?> destinationLat = const Value.absent(),
                Value<double?> destinationLng = const Value.absent(),
                required String idempotencyKey,
                Value<String> status = const Value.absent(),
                required String createdAt,
                Value<String?> lastError = const Value.absent(),
                Value<String?> paymentMethod = const Value.absent(),
                Value<int?> paymentAmountCents = const Value.absent(),
                Value<String?> splitJson = const Value.absent(),
                Value<String?> payIdempotencyKey = const Value.absent(),
              }) => OutboxOrdersCompanion.insert(
                id: id,
                customerId: customerId,
                itemsJson: itemsJson,
                promotionCode: promotionCode,
                redeemPoints: redeemPoints,
                destinationAddress: destinationAddress,
                destinationLat: destinationLat,
                destinationLng: destinationLng,
                idempotencyKey: idempotencyKey,
                status: status,
                createdAt: createdAt,
                lastError: lastError,
                paymentMethod: paymentMethod,
                paymentAmountCents: paymentAmountCents,
                splitJson: splitJson,
                payIdempotencyKey: payIdempotencyKey,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OutboxOrdersTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OutboxOrdersTable,
      OutboxOrder,
      $$OutboxOrdersTableFilterComposer,
      $$OutboxOrdersTableOrderingComposer,
      $$OutboxOrdersTableAnnotationComposer,
      $$OutboxOrdersTableCreateCompanionBuilder,
      $$OutboxOrdersTableUpdateCompanionBuilder,
      (
        OutboxOrder,
        BaseReferences<_$AppDatabase, $OutboxOrdersTable, OutboxOrder>,
      ),
      OutboxOrder,
      PrefetchHooks Function()
    >;
typedef $$OutboxPaymentsTableCreateCompanionBuilder =
    OutboxPaymentsCompanion Function({
      Value<int> id,
      required int orderId,
      required String method,
      required int amountCents,
      required String idempotencyKey,
      Value<String> status,
      required String createdAt,
      Value<String?> lastError,
    });
typedef $$OutboxPaymentsTableUpdateCompanionBuilder =
    OutboxPaymentsCompanion Function({
      Value<int> id,
      Value<int> orderId,
      Value<String> method,
      Value<int> amountCents,
      Value<String> idempotencyKey,
      Value<String> status,
      Value<String> createdAt,
      Value<String?> lastError,
    });

class $$OutboxPaymentsTableFilterComposer
    extends Composer<_$AppDatabase, $OutboxPaymentsTable> {
  $$OutboxPaymentsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get orderId => $composableBuilder(
    column: $table.orderId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get method => $composableBuilder(
    column: $table.method,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get amountCents => $composableBuilder(
    column: $table.amountCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OutboxPaymentsTableOrderingComposer
    extends Composer<_$AppDatabase, $OutboxPaymentsTable> {
  $$OutboxPaymentsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get orderId => $composableBuilder(
    column: $table.orderId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get method => $composableBuilder(
    column: $table.method,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get amountCents => $composableBuilder(
    column: $table.amountCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OutboxPaymentsTableAnnotationComposer
    extends Composer<_$AppDatabase, $OutboxPaymentsTable> {
  $$OutboxPaymentsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<int> get orderId =>
      $composableBuilder(column: $table.orderId, builder: (column) => column);

  GeneratedColumn<String> get method =>
      $composableBuilder(column: $table.method, builder: (column) => column);

  GeneratedColumn<int> get amountCents => $composableBuilder(
    column: $table.amountCents,
    builder: (column) => column,
  );

  GeneratedColumn<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => column,
  );

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);
}

class $$OutboxPaymentsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OutboxPaymentsTable,
          OutboxPayment,
          $$OutboxPaymentsTableFilterComposer,
          $$OutboxPaymentsTableOrderingComposer,
          $$OutboxPaymentsTableAnnotationComposer,
          $$OutboxPaymentsTableCreateCompanionBuilder,
          $$OutboxPaymentsTableUpdateCompanionBuilder,
          (
            OutboxPayment,
            BaseReferences<_$AppDatabase, $OutboxPaymentsTable, OutboxPayment>,
          ),
          OutboxPayment,
          PrefetchHooks Function()
        > {
  $$OutboxPaymentsTableTableManager(
    _$AppDatabase db,
    $OutboxPaymentsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OutboxPaymentsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OutboxPaymentsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OutboxPaymentsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int> orderId = const Value.absent(),
                Value<String> method = const Value.absent(),
                Value<int> amountCents = const Value.absent(),
                Value<String> idempotencyKey = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
              }) => OutboxPaymentsCompanion(
                id: id,
                orderId: orderId,
                method: method,
                amountCents: amountCents,
                idempotencyKey: idempotencyKey,
                status: status,
                createdAt: createdAt,
                lastError: lastError,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required int orderId,
                required String method,
                required int amountCents,
                required String idempotencyKey,
                Value<String> status = const Value.absent(),
                required String createdAt,
                Value<String?> lastError = const Value.absent(),
              }) => OutboxPaymentsCompanion.insert(
                id: id,
                orderId: orderId,
                method: method,
                amountCents: amountCents,
                idempotencyKey: idempotencyKey,
                status: status,
                createdAt: createdAt,
                lastError: lastError,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OutboxPaymentsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OutboxPaymentsTable,
      OutboxPayment,
      $$OutboxPaymentsTableFilterComposer,
      $$OutboxPaymentsTableOrderingComposer,
      $$OutboxPaymentsTableAnnotationComposer,
      $$OutboxPaymentsTableCreateCompanionBuilder,
      $$OutboxPaymentsTableUpdateCompanionBuilder,
      (
        OutboxPayment,
        BaseReferences<_$AppDatabase, $OutboxPaymentsTable, OutboxPayment>,
      ),
      OutboxPayment,
      PrefetchHooks Function()
    >;
typedef $$OutboxEventsTableCreateCompanionBuilder =
    OutboxEventsCompanion Function({
      Value<int> id,
      required String eventType,
      required String clientEventId,
      required String payloadJson,
      required String idempotencyKey,
      Value<String> status,
      required String createdAt,
      Value<String?> lastError,
    });
typedef $$OutboxEventsTableUpdateCompanionBuilder =
    OutboxEventsCompanion Function({
      Value<int> id,
      Value<String> eventType,
      Value<String> clientEventId,
      Value<String> payloadJson,
      Value<String> idempotencyKey,
      Value<String> status,
      Value<String> createdAt,
      Value<String?> lastError,
    });

class $$OutboxEventsTableFilterComposer
    extends Composer<_$AppDatabase, $OutboxEventsTable> {
  $$OutboxEventsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get eventType => $composableBuilder(
    column: $table.eventType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get clientEventId => $composableBuilder(
    column: $table.clientEventId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OutboxEventsTableOrderingComposer
    extends Composer<_$AppDatabase, $OutboxEventsTable> {
  $$OutboxEventsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get eventType => $composableBuilder(
    column: $table.eventType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get clientEventId => $composableBuilder(
    column: $table.clientEventId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OutboxEventsTableAnnotationComposer
    extends Composer<_$AppDatabase, $OutboxEventsTable> {
  $$OutboxEventsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get eventType =>
      $composableBuilder(column: $table.eventType, builder: (column) => column);

  GeneratedColumn<String> get clientEventId => $composableBuilder(
    column: $table.clientEventId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => column,
  );

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);
}

class $$OutboxEventsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OutboxEventsTable,
          OutboxEvent,
          $$OutboxEventsTableFilterComposer,
          $$OutboxEventsTableOrderingComposer,
          $$OutboxEventsTableAnnotationComposer,
          $$OutboxEventsTableCreateCompanionBuilder,
          $$OutboxEventsTableUpdateCompanionBuilder,
          (
            OutboxEvent,
            BaseReferences<_$AppDatabase, $OutboxEventsTable, OutboxEvent>,
          ),
          OutboxEvent,
          PrefetchHooks Function()
        > {
  $$OutboxEventsTableTableManager(_$AppDatabase db, $OutboxEventsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OutboxEventsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OutboxEventsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OutboxEventsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> eventType = const Value.absent(),
                Value<String> clientEventId = const Value.absent(),
                Value<String> payloadJson = const Value.absent(),
                Value<String> idempotencyKey = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
              }) => OutboxEventsCompanion(
                id: id,
                eventType: eventType,
                clientEventId: clientEventId,
                payloadJson: payloadJson,
                idempotencyKey: idempotencyKey,
                status: status,
                createdAt: createdAt,
                lastError: lastError,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String eventType,
                required String clientEventId,
                required String payloadJson,
                required String idempotencyKey,
                Value<String> status = const Value.absent(),
                required String createdAt,
                Value<String?> lastError = const Value.absent(),
              }) => OutboxEventsCompanion.insert(
                id: id,
                eventType: eventType,
                clientEventId: clientEventId,
                payloadJson: payloadJson,
                idempotencyKey: idempotencyKey,
                status: status,
                createdAt: createdAt,
                lastError: lastError,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OutboxEventsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OutboxEventsTable,
      OutboxEvent,
      $$OutboxEventsTableFilterComposer,
      $$OutboxEventsTableOrderingComposer,
      $$OutboxEventsTableAnnotationComposer,
      $$OutboxEventsTableCreateCompanionBuilder,
      $$OutboxEventsTableUpdateCompanionBuilder,
      (
        OutboxEvent,
        BaseReferences<_$AppDatabase, $OutboxEventsTable, OutboxEvent>,
      ),
      OutboxEvent,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$DriftProductsTableTableManager get driftProducts =>
      $$DriftProductsTableTableManager(_db, _db.driftProducts);
  $$DriftCategoriesTableTableManager get driftCategories =>
      $$DriftCategoriesTableTableManager(_db, _db.driftCategories);
  $$SyncMetaTableTableManager get syncMeta =>
      $$SyncMetaTableTableManager(_db, _db.syncMeta);
  $$OutboxOrdersTableTableManager get outboxOrders =>
      $$OutboxOrdersTableTableManager(_db, _db.outboxOrders);
  $$OutboxPaymentsTableTableManager get outboxPayments =>
      $$OutboxPaymentsTableTableManager(_db, _db.outboxPayments);
  $$OutboxEventsTableTableManager get outboxEvents =>
      $$OutboxEventsTableTableManager(_db, _db.outboxEvents);
}
