import request from './request'

export function getPredictionList(params) {
  return request.get('/failure-predictions', { params })
}

export function getPredictionDetail(id) {
  return request.get(`/failure-predictions/${id}`)
}

export function generatePrediction() {
  return request.post('/failure-predictions/generate')
}

export function getPredictionStatistics() {
  return request.get('/failure-predictions/statistics')
}
