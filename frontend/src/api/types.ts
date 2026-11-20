/** DTOs mirroring the backend camelCase JSON boundary schemas. */

export interface ApiErrorDetail {
  code: string;
  message: string;
  field?: string | null;
}

export interface ErrorResponse {
  code: string;
  message: string;
  field?: string | null;
  details: ApiErrorDetail[];
  requestId?: string;
  category?: 'permanent' | 'transient';
  retryAfterSeconds?: number | null;
}

export interface CursorPage<T> {
  items: T[];
  nextCursor: string | null;
  hasMore: boolean;
}

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface UserResponse {
  id: string;
  email: string;
  displayName: string;
  systemRole: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface MembershipResponse {
  id: string;
  userId: string;
  organisationId: string;
  role: string;
  isActive: boolean;
  createdAt: string;
}

export interface AuthMeResponse extends UserResponse {
  memberships: MembershipResponse[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  user: UserResponse;
}

export interface HealthResponse {
  status: string;
  database: string;
  postgisVersion: string | null;
  storageRootReady: boolean;
}

export type TimePrecision = 'exact' | 'approximate' | 'range' | 'unknown';
export type LocationPrecision = 'exact' | 'approximate' | 'area' | 'unknown';
export type AccessClass = 'public' | 'internal' | 'restricted' | 'high_sensitivity';
export type SourceType =
  | 'community_anonymous'
  | 'community_registered'
  | 'field_team'
  | 'sensor'
  | 'laboratory'
  | 'remote_sensing'
  | 'institutional_record'
  | 'research';

export interface CreateObservationRequest {
  idempotencyKey: string;
  organisationId?: string;
  observationType: string;
  sourceType?: SourceType;
  description: string;
  isFirsthand?: boolean;
  eventStartAt?: string;
  observedAt?: string;
  submittedAt?: string;
  timePrecision: TimePrecision;
  originalTimeWording?: string;
  lat?: number;
  lon?: number;
  locationPrecision: LocationPrecision;
  originalLocationWording?: string;
  accessClass: AccessClass;
}

export interface IntakeReceiptResponse {
  observationId: string;
  organisationId: string;
  receivedAt: string;
  observationType: string;
  timePrecision: TimePrecision;
  locationPrecision: LocationPrecision;
  currentVersion: number;
  trackingCode: string | null;
  idempotentReplay: boolean;
}

export interface ObservationSummary {
  id: string;
  organisationId: string;
  observationType: string;
  sourceType: SourceType;
  description: string;
  isFirsthand?: boolean | null;
  eventStartAt?: string | null;
  observedAt?: string | null;
  submittedAt?: string | null;
  receivedAt: string;
  timePrecision: TimePrecision;
  originalTimeWording?: string | null;
  publicLocation: GeoPoint | null;
  locationPrecision: LocationPrecision;
  qualityFlags: string[];
  accessClass: AccessClass;
  isHidden: boolean;
  currentVersion: number;
  createdAt: string;
  updatedAt: string;
}

export interface ObservationDetail extends ObservationSummary {
  /** Restricted staff/owner view only; never present on the public summary DTO. */
  originalLocationWording?: string | null;
  location?: GeoPoint | null;
  submittedByUserId?: string | null;
}

export interface CaseObservation {
  id: string;
  observationId: string;
  linkRationale: string;
  reviewStatus: string;
  isContested: boolean;
  createdAt: string;
}

export interface CaseSummary {
  id: string;
  organisationId: string;
  caseCode: string;
  title: string;
  summary: string;
  status: string;
  statusRationale: string;
  investigationQuestions: string[];
  competingHypotheses: string[];
  evidenceGaps: string[];
  accessClass: string;
  isPublicSummaryApproved: boolean;
  publicSummary: string | null;
  lastReviewedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CaseDetail extends CaseSummary {
  observations: CaseObservation[];
}

export interface TimelineItem {
  dateType: string;
  timestamp: string;
  precision: string;
  source: string;
  entityType: string;
  entityId: string;
  summary?: string | null;
}

export interface CorrelationSuggestion {
  id: string;
  organisationId: string;
  observationAId: string;
  observationBId: string;
  task: string;
  /** Ranking signal only: not a probability, severity, or causation claim. */
  score: number;
  components: Record<string, number>;
  missingSignals: string[];
  reasons: string[];
  sourceIndependent: boolean;
  ambiguous: boolean;
  status: string;
  methodVersion: string;
  decidedByUserId?: string | null;
  decidedAt?: string | null;
  decisionReason?: string | null;
  createdAt: string;
}

export type CorrelationDecision = 'accepted' | 'rejected' | 'ambiguous';

/** Unauthenticated receipt lookup: high-entropy code in, PII-free receipt out. */
export interface ReceiptLookupRequest {
  trackingCode: string;
}

export interface ReceiptLookupResponse {
  observationId: string;
  receivedAt: string;
  observationType: string;
  timePrecision: TimePrecision;
  locationPrecision: LocationPrecision;
  evidenceCount: number;
}

/** Approved public case summary. Internal notes, identities and exact geometry are absent. */
export interface PublicCaseSummary {
  id: string;
  caseCode: string;
  title: string;
  status: string;
  publicSummary: string;
  publicGeometry?: string | null;
  areaReference?: string | null;
  lastReviewedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

/** EXIF-stripped derivative metadata. Bytes are fetched separately, never inlined. */
export interface AssetDerivativeResponse {
  id: string;
  parentAssetId: string;
  derivativeType: string;
  mimeType: string;
  sizeBytes: number;
  sha256Checksum: string;
  exifStripped: boolean;
  accessClass: string;
  createdAt: string;
}

/** Durable upload receipt. Storage keys and file contents are not exposed here. */
export interface EvidenceAssetResponse {
  id: string;
  observationId: string;
  organisationId: string;
  originalFilename: string;
  declaredMimeType: string;
  detectedMimeType: string;
  sizeBytes: number;
  sha256Checksum: string;
  scanStatus: string;
  metadataExtractionStatus: string;
  accessClass: string;
  receivedAt: string;
  createdAt: string;
  derivatives: AssetDerivativeResponse[];
  idempotentReplay: boolean;
}

/** Read-only administration summaries. Only fields safe for a staff view are declared. */
export interface OrganisationSummary {
  id: string;
  name: string;
  orgType: string;
  isActive: boolean;
  createdAt: string;
}

export interface AuditEventSummary {
  id: string;
  occurredAt: string;
  actorRole: string;
  action: string;
  targetType: string;
}

export interface JobTypeSummary {
  jobType: string;
  pending: number;
  processing: number;
  processed: number;
  failed: number;
  dead: number;
}

export interface JobSummaryResponse {
  totalPending: number;
  totalProcessing: number;
  totalProcessed: number;
  totalFailed: number;
  totalDead: number;
  byType: JobTypeSummary[];
}

/** Phase 3 read DTOs (ADR-037). Geometry WKT and storage keys are server metadata. */

export interface EnvironmentalEntityResponse {
  id: string;
  organisationId: string;
  entityType: string;
  name: string;
  description: string | null;
  geometry: string | null;
  crs: string;
  parentEntityId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface EnvironmentalRelationshipResponse {
  id: string;
  organisationId: string;
  relationshipType: string;
  fromEntityId: string | null;
  fromObservationId: string | null;
  toEntityId: string | null;
  toObservationId: string | null;
  spatialScope: string | null;
  temporalStartAt: string | null;
  temporalEndAt: string | null;
  evidenceSummary: string;
  supportingEvidenceAssetIds: string[];
  methodName: string;
  methodVersion: string;
  uncertainty: string;
  uncertaintyNote: string;
  alternativeExplanations: string;
  reviewState: string;
  reviewedByUserId: string | null;
  reviewedAt: string | null;
  createdAt: string;
}

export interface AnalysisRunResponse {
  id: string;
  organisationId: string;
  caseId: string | null;
  question: string;
  analysisType: string;
  methodName: string;
  methodVersion: string;
  parameters: Record<string, unknown>;
  inputDatasetVersionIds: string[];
  crs: string;
  qualityMaskNotes: string | null;
  seasonalContext: string | null;
  limitations: string;
  status: string;
  requestedByUserId: string | null;
  startedAt: string | null;
  completedAt: string | null;
  failureReason: string | null;
  createdAt: string;
}

export interface AnalysisOutputResponse {
  id: string;
  analysisRunId: string;
  outputType: string;
  summary: string;
  storageKey: string | null;
  isDerived: boolean;
  derivedFromObservationIds: string[];
  interpretationState: string;
  limitations: string;
  createdAt: string;
}

export interface DatasetResponse {
  id: string;
  organisationId: string;
  name: string;
  description: string | null;
  owner: string;
  licence: string;
  attribution: string;
  permittedUse: string;
  crs: string;
  coverageStartAt: string | null;
  coverageEndAt: string | null;
  coverageGeometry: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetVersionResponse {
  id: string;
  datasetId: string;
  versionLabel: string;
  sourceAcquisitionAt: string;
  resolution: string;
  crs: string;
  method: string;
  limitations: string | null;
  qualityNotes: string | null;
  licenceSnapshot: string;
  attributionSnapshot: string;
  permittedUseSnapshot: string;
  checksum: string | null;
  storageKey: string | null;
  createdAt: string;
}

export interface PrioritisationAssessmentResponse {
  id: string;
  organisationId: string;
  caseId: string;
  assessmentAt: string;
  methodName: string;
  methodVersion: string;
  factors: Record<string, unknown>;
  missingInputs: string[];
  compositeRank: number | null;
  rankingMethodRef: string | null;
  rankIsNotSeverity: boolean | null;
  decision: string | null;
  decisionRationale: string | null;
  decidedByUserId: string | null;
  reviewerUserId: string | null;
  decidedAt: string | null;
  reviewedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface InterventionResponse {
  id: string;
  organisationId: string;
  caseId: string;
  additionalCaseIds: string[];
  objective: string;
  rationale: string | null;
  responsibleOrganisationId: string;
  authorisedLeadUserId: string;
  approvalReference: string | null;
  location: string | null;
  affectedAreaNotes: string | null;
  plannedStartAt: string | null;
  plannedEndAt: string | null;
  actualStartAt: string | null;
  actualEndAt: string | null;
  status: string;
  resourcesNotes: string | null;
  intendedOutcome: string | null;
  baselineSummary: string | null;
  risks: string | null;
  limitations: string | null;
  followUpSchedule: string | null;
  indicatorDefinitionIds: string[];
  verificationAssessmentId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface MilestoneResponse {
  id: string;
  interventionId: string;
  name: string;
  description: string | null;
  plannedAt: string | null;
  completedAt: string | null;
  status: string;
  evidenceAssetIds: string[];
  createdAt: string;
  updatedAt: string;
}

export interface IndicatorResponse {
  id: string;
  organisationId: string;
  unitId: string;
  code: string;
  name: string;
  domain: string;
  description: string | null;
  methodName: string;
  methodVersion: string;
  criteriaVersion: string | null;
  approvedByUserId: string | null;
  approvedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface MeasurementResponse {
  id: string;
  organisationId: string;
  indicatorDefinitionId: string;
  unitId: string;
  interventionId: string | null;
  caseId: string | null;
  observationId: string | null;
  measuredAt: string;
  value: number | null;
  qualifier: string;
  detectionLimit: number | null;
  methodName: string;
  methodVersion: string;
  qualityControls: string | null;
  uncertaintyNote: string | null;
  source: string | null;
  createdAt: string;
}

export interface VerificationAssessmentResponse {
  id: string;
  organisationId: string;
  interventionId: string;
  baselineMeasurementIds: string[];
  followUpMeasurementIds: string[];
  comparisonMethod: string;
  conclusion: string;
  status: string;
  confounders: string | null;
  seasonalityNotes: string | null;
  uncertaintyNote: string | null;
  criteriaVersion: string | null;
  reviewedByUserId: string | null;
  reviewedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface PublicationResponse {
  id: string;
  organisationId: string;
  verificationAssessmentId: string | null;
  caseId: string | null;
  publishedText: string;
  approvedByUserId: string;
  approvedRole: string;
  approvedAt: string;
  retractedAt: string | null;
  retractionReason: string | null;
  createdAt: string;
}

export interface UnitResponse {
  id: string;
  symbol: string;
  name: string;
  dimension: string;
  ucumCode: string | null;
}

export interface CreateOrganisationRequest {
  name: string;
  orgType: string;
  isActive?: boolean;
}

export interface CreateUserRequest {
  email: string;
  displayName: string;
  password: string;
  systemRole?: string | null;
  isActive?: boolean;
}

export interface UpdateUserRequest {
  displayName?: string | null;
  systemRole?: string | null;
  isActive?: boolean | null;
}

export interface UpdateOrganisationRequest {
  name?: string | null;
  orgType?: string | null;
  isActive?: boolean | null;
}

export interface AssignMembershipRequest {
  userId: string;
  role: string;
  isActive?: boolean;
  reason?: string | null;
}

export interface CreateDatasetRequest {
  organisationId: string;
  name: string;
  owner: string;
  licence: string;
  attribution: string;
  permittedUse: string;
  crs: string;
  description?: string | null;
  coverageGeometry?: string | null;
}

export interface AddDatasetVersionRequest {
  organisationId: string;
  versionLabel: string;
  sourceAcquisitionAt: string;
  resolution: string;
  crs: string;
  method: string;
  licence: string;
  attribution: string;
  permittedUse: string;
  limitations?: string | null;
  qualityNotes?: string | null;
}

export interface CreateEntityRequest {
  organisationId: string;
  entityType: string;
  name: string;
  crs?: string;
  description?: string | null;
  geometry?: string | null;
}

export interface ProposeRelationshipRequest {
  organisationId: string;
  relationshipType: string;
  evidenceSummary: string;
  uncertainty: string;
  uncertaintyNote: string;
  alternativeExplanations: string;
  methodName: string;
  methodVersion: string;
  fromEntityId?: string | null;
  toEntityId?: string | null;
}

export interface QueueAnalysisRequest {
  organisationId: string;
  question: string;
  analysisType: string;
  methodName: string;
  methodVersion: string;
  inputDatasetVersionIds: string[];
  crs: string;
  limitations: string;
  caseId?: string | null;
}

export interface CreatePrioritisationAssessmentRequest {
  organisationId: string;
  caseId: string;
  methodName: string;
  methodVersion: string;
  compositeRank?: number | null;
  rankingMethodRef?: string | null;
  rankIsNotSeverity?: boolean | null;
}

export interface RecordPrioritisationDecisionRequest {
  organisationId: string;
  decision: string;
  rationale: string;
}

export interface CreateInterventionRequest {
  organisationId: string;
  caseId: string;
  objective: string;
  responsibleOrganisationId: string;
  authorisedLeadUserId: string;
  rationale?: string | null;
  location?: string | null;
}

export interface AddMilestoneRequest {
  organisationId: string;
  name: string;
  description?: string | null;
}

export interface TransitionInterventionRequest {
  organisationId: string;
  targetStatus: string;
  rationale: string;
}

export interface CreateIndicatorRequest {
  organisationId: string;
  code: string;
  name: string;
  domain: string;
  unitId: string;
  methodName: string;
  methodVersion: string;
  description?: string | null;
}

export interface RecordMeasurementRequest {
  organisationId: string;
  measuredAt: string;
  qualifier: string;
  unitId: string;
  methodName: string;
  methodVersion: string;
  value?: number | null;
  detectionLimit?: number | null;
  interventionId?: string | null;
}

export interface CreateVerificationAssessmentRequest {
  organisationId: string;
  interventionId: string;
  comparisonMethod: string;
  direction: string;
  baselineValues?: number[];
  followUpValues?: number[];
  confounders?: string | null;
  uncertaintyNote?: string | null;
}

export interface PublishSummaryRequest {
  organisationId: string;
  publishedText: string;
  verificationAssessmentId?: string | null;
  caseId?: string | null;
}
