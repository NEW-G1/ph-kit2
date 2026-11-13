-- raw_locations: 원천 fdic_banks.locations 전체를 당일 snapshot_date 파티션에 가공 없이 복사한다.
-- 적재 방식: snapshot (contract load.mode). 멱등 3문장 패턴 (sql_rules.md §1)

-- (1) 테이블이 없을 때만 생성
CREATE TABLE IF NOT EXISTS `{{ project }}.{{ dataset_raw }}.raw_locations`
(
  snapshot_date DATE OPTIONS (description = '실행 날짜 (Airflow ds). 파티션 키'),
  fdic_certificate_number STRING OPTIONS (description = 'FDIC가 금융기관에 부여한 고유 번호'),
  institution_name STRING OPTIONS (description = '금융기관의 법적 명칭'),
  branch_name STRING OPTIONS (description = '지점 이름'),
  branch_number STRING OPTIONS (description = '지점에 해당하는 사무소 번호'),
  main_office BOOL OPTIONS (description = '기관의 본점이면 TRUE'),
  branch_address STRING OPTIONS (description = '지점이 위치한 도로명 주소 (기관 소재지)'),
  branch_city STRING OPTIONS (description = '지점이 위치한 도시'),
  zip_code STRING OPTIONS (description = '지점 소재지 우편번호 앞 5자리'),
  branch_county STRING OPTIONS (description = '지점이 위치한 카운티'),
  county_fips_code STRING OPTIONS (description = '주와 카운티를 나타내는 5자리 FIPS 코드'),
  state STRING OPTIONS (description = '지점이 위치한 주 약어'),
  state_name STRING OPTIONS (description = '지점이 위치한 주 이름'),
  institution_class STRING OPTIONS (description = 'FDIC가 헌장 유형, 감독기관 등에 따라 부여한 기관 분류 코드'),
  cbsa_fips_code STRING OPTIONS (description = '핵심 기반 통계 지역(CBSA) 코드'),
  cbsa_name STRING OPTIONS (description = '핵심 기반 통계 지역(CBSA) 이름'),
  cbsa_division_flag BOOL OPTIONS (description = 'CBSA 구역 소속 여부'),
  cbsa_division_fips_code INT64 OPTIONS (description = 'CBSA 구역 코드'),
  cbsa_division_name STRING OPTIONS (description = 'CBSA 구역 이름'),
  cbsa_metro_flag BOOL OPTIONS (description = '대도시 통계 지역 소속 여부'),
  cbsa_metro_fips_code STRING OPTIONS (description = '대도시 통계 지역 코드'),
  cbsa_metro_name STRING OPTIONS (description = '대도시 통계 지역 이름'),
  cbsa_micro_flag BOOL OPTIONS (description = '소도시 통계 지역 소속 여부'),
  csa_flag BOOL OPTIONS (description = '통합 통계 지역(CSA) 소속 여부'),
  csa_fips_code STRING OPTIONS (description = '통합 통계 지역(CSA) 코드'),
  csa_name STRING OPTIONS (description = '통합 통계 지역(CSA) 이름'),
  date_established DATE OPTIONS (description = '지점이 영업을 시작한 날짜'),
  fdic_uninum STRING OPTIONS (description = '지점을 소유한 기관의 FDIC UNINUM'),
  last_updated DATE OPTIONS (description = '기관 정보가 갱신된 날짜'),
  service_type STRING OPTIONS (description = '사무소 유형 코드 (11~16 풀서비스, 21~30 제한서비스)'),
  branch_fdic_uninum STRING OPTIONS (description = 'FDIC가 지점에 부여한 고유 식별 번호. 사무소 1곳의 키')
)
PARTITION BY snapshot_date
CLUSTER BY branch_fdic_uninum, date_established
OPTIONS (
  partition_expiration_days = 7,
  description = '원천 사무소 위치 원본. 소스: bigquery-public-data.fdic_banks.locations. 원천 1행 = 1행 (사무소 1곳), snapshot_date 파티션마다 원천 전체를 가공 없이 복사'
);

-- (2) 당일 파티션 삭제
DELETE FROM `{{ project }}.{{ dataset_raw }}.raw_locations`
WHERE snapshot_date = DATE('{{ ds }}');

-- (3) 당일 파티션 적재 (원천 전체 복사, 컬럼 이름으로 명시)
INSERT INTO `{{ project }}.{{ dataset_raw }}.raw_locations`
  (snapshot_date, fdic_certificate_number, institution_name, branch_name, branch_number,
   main_office, branch_address, branch_city, zip_code, branch_county, county_fips_code,
   state, state_name, institution_class, cbsa_fips_code, cbsa_name, cbsa_division_flag,
   cbsa_division_fips_code, cbsa_division_name, cbsa_metro_flag, cbsa_metro_fips_code,
   cbsa_metro_name, cbsa_micro_flag, csa_flag, csa_fips_code, csa_name, date_established,
   fdic_uninum, last_updated, service_type, branch_fdic_uninum)
SELECT
  DATE('{{ ds }}') AS snapshot_date,
  fdic_certificate_number,
  institution_name,
  branch_name,
  branch_number,
  main_office,
  branch_address,
  branch_city,
  zip_code,
  branch_county,
  county_fips_code,
  state,
  state_name,
  institution_class,
  cbsa_fips_code,
  cbsa_name,
  cbsa_division_flag,
  cbsa_division_fips_code,
  cbsa_division_name,
  cbsa_metro_flag,
  cbsa_metro_fips_code,
  cbsa_metro_name,
  cbsa_micro_flag,
  csa_flag,
  csa_fips_code,
  csa_name,
  date_established,
  fdic_uninum,
  last_updated,
  service_type,
  branch_fdic_uninum
FROM `bigquery-public-data.fdic_banks.locations`;
