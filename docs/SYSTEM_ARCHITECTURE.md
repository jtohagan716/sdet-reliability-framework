\# SDET Reliability Framework - System Architecture



\## Purpose



The SDET Reliability Framework is a quality engineering platform designed to evaluate whether an application is ready for release.



The framework combines automated testing, runtime health checks, observability validation, and release assessment into one evidence-driven quality process.



\## High-Level Architecture



```text

GitHub Actions

     |

     v

Docker / Docker Compose

     |

     v

FastAPI Application

     |

     +--> Health Endpoint

     +--> Metrics Endpoint

     |

     v

Prometheus

     |

     v

Grafana



Playwright Tests

     |

     v

Playwright JSON Results

     |

     v

QualitySignal



Runtime Health Checks

     |

     v

QualitySignal



QualitySignal Objects

     |

     v

ReleaseAssessment

     |

     v

Release Readiness Report

