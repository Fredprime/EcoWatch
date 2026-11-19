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

/** Durable upload receipt. Storage keys and file contents are not exposed here. */
export interface EvidenceAssetResponse {
  id: string;
  observationId: string;
  originalFilename: string;
  detectedMimeType: string;
  sizeBytes: number;
  sha256Checksum: string;
  scanStatus: string;
  receivedAt: string;
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
