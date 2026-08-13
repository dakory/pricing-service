// @ts-nocheck
"use client";

import React from "react";
import { Button, IconButton, Input, Select } from "./design-system";

const columns = Array.from({ length: 10 });
const properties = Array.from({ length: 3 });

/** Mirrors the calendar layout while the pricing data request is pending. */
export function CalendarLoadingSkeleton({ bodyOnly = false }: { bodyOnly?: boolean }) {
  return (
    <div className={`calendar-loading-skeleton${bodyOnly ? " calendar-loading-skeleton-body" : ""}`} aria-label="Loading calendar" aria-busy="true">
      {!bodyOnly && <div className="calendar-loading-toolbar">
        <div className="calendar-loading-toolbar-left">
          <div className="calendar-loading-select">
            <Select value="" options={[{ label: " ", value: "" }]} onChange={() => {}} />
            <span className="calendar-skeleton calendar-skeleton-toolbar-month" aria-hidden="true" />
          </div>
          <Button variant="secondary" size="sm" onClick={() => {}}>Today</Button>
        </div>
        <div className="calendar-loading-toolbar-actions">
          <Button variant="secondary" size="sm" onClick={() => {}}>Global settings</Button>
          <Button variant="secondary" size="sm" onClick={() => {}}>Actions</Button>
        </div>
      </div>}
      <div className="calendar-loading-grid" style={{ gridTemplateColumns: "280px repeat(10, 96px)", gridTemplateRows: "48px 52px 36px repeat(3, 70px)" }}>
        <div className="calendar-loading-corner">
          <span className="calendar-skeleton calendar-skeleton-property-count" />
          <div className="calendar-loading-search"><Input placeholder="Search listings..." value="" onChange={() => {}} /></div>
        </div>
        <div className="calendar-loading-month" style={{ gridColumn: "2 / -1", gridRow: 1 }}>
          <span className="calendar-skeleton calendar-skeleton-month-title" aria-hidden="true" />
        </div>
        {columns.map((_, index) => (
          <div key={`head-${index}`} className="calendar-loading-date" style={{ gridRow: 2 }}>
            <span className="calendar-skeleton calendar-skeleton-weekday" />
            <span className="calendar-skeleton calendar-skeleton-day" />
          </div>
        ))}
        <div className="calendar-loading-group" style={{ gridRow: 3 }}>
          <span className="calendar-skeleton calendar-skeleton-label calendar-skeleton-label-group" />
        </div>
        {columns.map((_, index) => <div key={`band-${index}`} className="calendar-loading-band" style={{ gridRow: 3 }} />)}
        {properties.map((_, propertyIndex) => (
          <React.Fragment key={`property-${propertyIndex}`}>
            <div className="calendar-loading-property">
              <span className="calendar-skeleton calendar-skeleton-avatar" />
              <span className="calendar-skeleton calendar-skeleton-label calendar-skeleton-label-property" />
            </div>
            {columns.map((__, columnIndex) => (
              <div key={`cell-${propertyIndex}-${columnIndex}`} className="calendar-loading-cell">
                <span className="calendar-skeleton calendar-skeleton-price" />
              </div>
            ))}
          </React.Fragment>
        ))}
      </div>
      <div className="calendar-loading-edge-shadow calendar-loading-edge-shadow-left" />
      <div className="calendar-loading-edge-shadow calendar-loading-edge-shadow-right" />
      <div className="calendar-loading-navigation calendar-loading-navigation-left"><IconButton label="Scroll earlier" onClick={() => {}} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-left.svg" style={{ width: 16, height: 16 }} alt="" />} /></div>
      <div className="calendar-loading-navigation calendar-loading-navigation-right"><IconButton label="Scroll later" onClick={() => {}} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-right.svg" style={{ width: 16, height: 16 }} alt="" />} /></div>
    </div>
  );
}
