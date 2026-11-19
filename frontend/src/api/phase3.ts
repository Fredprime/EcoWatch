import { request } from './client';
import type {
  AnalysisOutputResponse,
  AnalysisRunResponse,
  CursorPage,
  DatasetResponse,
  DatasetVersionResponse,
  EnvironmentalEntityResponse,
  EnvironmentalRelationshipResponse,
  IndicatorResponse,
  InterventionResponse,
  MeasurementResponse,
  MilestoneResponse,
  PrioritisationAssessmentResponse,
  PublicationResponse,
  VerificationAssessmentResponse,
} from './types';

const BASE = '/api/v1';

/** Cursor pagination is bounded server-side; this view shows one page at a time. */
function pageQuery(cursor?: string | null): string {
  return cursor ? `?cursor=${encodeURIComponent(cursor)}&limit=50` : '?limit=50';
}

/**
 * Read-only Phase 3 list helpers (ADR-037). Permission and organisation scoping
 * are enforced by the server; these calls never send a client-side role check.
 * Child collections need their parent id because the rows carry no own org scope.
 */

// Intelligence
export function listIntelligenceEntities(
  cursor?: string | null,
): Promise<CursorPage<EnvironmentalEntityResponse>> {
  return request<CursorPage<EnvironmentalEntityResponse>>(
    `${BASE}/intelligence/entities${pageQuery(cursor)}`,
  );
}

export function listIntelligenceRelationships(
  cursor?: string | null,
): Promise<CursorPage<EnvironmentalRelationshipResponse>> {
  return request<CursorPage<EnvironmentalRelationshipResponse>>(
    `${BASE}/intelligence/relationships${pageQuery(cursor)}`,
  );
}

export function listAnalysisRuns(cursor?: string | null): Promise<CursorPage<AnalysisRunResponse>> {
  return request<CursorPage<AnalysisRunResponse>>(
    `${BASE}/intelligence/analyses${pageQuery(cursor)}`,
  );
}

export function listAnalysisOutputs(
  analysisRunId: string,
  cursor?: string | null,
): Promise<CursorPage<AnalysisOutputResponse>> {
  return request<CursorPage<AnalysisOutputResponse>>(
    `${BASE}/intelligence/analyses/${encodeURIComponent(analysisRunId)}/outputs${pageQuery(cursor)}`,
  );
}

// Catalogue
export function listDatasets(cursor?: string | null): Promise<CursorPage<DatasetResponse>> {
  return request<CursorPage<DatasetResponse>>(`${BASE}/catalogue/datasets${pageQuery(cursor)}`);
}

export function listDatasetVersions(
  datasetId: string,
  cursor?: string | null,
): Promise<CursorPage<DatasetVersionResponse>> {
  return request<CursorPage<DatasetVersionResponse>>(
    `${BASE}/catalogue/datasets/${encodeURIComponent(datasetId)}/versions${pageQuery(cursor)}`,
  );
}

// Prioritisation
export function listPrioritisationAssessments(
  cursor?: string | null,
): Promise<CursorPage<PrioritisationAssessmentResponse>> {
  return request<CursorPage<PrioritisationAssessmentResponse>>(
    `${BASE}/prioritisation/assessments${pageQuery(cursor)}`,
  );
}

// Interventions — the router prefix and route both use "interventions".
export function listInterventions(
  cursor?: string | null,
): Promise<CursorPage<InterventionResponse>> {
  return request<CursorPage<InterventionResponse>>(
    `${BASE}/interventions/interventions${pageQuery(cursor)}`,
  );
}

export function listMilestones(
  interventionId: string,
  cursor?: string | null,
): Promise<CursorPage<MilestoneResponse>> {
  return request<CursorPage<MilestoneResponse>>(
    `${BASE}/interventions/interventions/${encodeURIComponent(interventionId)}/milestones${pageQuery(cursor)}`,
  );
}

// Verification
export function listIndicators(cursor?: string | null): Promise<CursorPage<IndicatorResponse>> {
  return request<CursorPage<IndicatorResponse>>(`${BASE}/verification/indicators${pageQuery(cursor)}`);
}

export function listMeasurements(
  cursor?: string | null,
): Promise<CursorPage<MeasurementResponse>> {
  return request<CursorPage<MeasurementResponse>>(
    `${BASE}/verification/measurements${pageQuery(cursor)}`,
  );
}

export function listVerificationAssessments(
  cursor?: string | null,
): Promise<CursorPage<VerificationAssessmentResponse>> {
  return request<CursorPage<VerificationAssessmentResponse>>(
    `${BASE}/verification/assessments${pageQuery(cursor)}`,
  );
}

export function listPublications(cursor?: string | null): Promise<CursorPage<PublicationResponse>> {
  return request<CursorPage<PublicationResponse>>(
    `${BASE}/verification/publications${pageQuery(cursor)}`,
  );
}
