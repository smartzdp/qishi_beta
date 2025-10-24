import React, { useEffect, useRef } from 'react'
import Plotly from 'plotly.js-dist-min'

function PlotlyChart({ figure }) {
  const plotRef = useRef(null)

  useEffect(() => {
    if (plotRef.current && figure) {
      try {
        // Parse figure if it's a string
        const figData = typeof figure === 'string' ? JSON.parse(figure) : figure
        
        Plotly.newPlot(
          plotRef.current,
          figData.data,
          figData.layout || {},
          { responsive: true }
        )
      } catch (err) {
        console.error('Failed to render Plotly chart:', err)
      }
    }
  }, [figure])

  return (
    <div className="plotly-chart">
      <div ref={plotRef}></div>
    </div>
  )
}

export default PlotlyChart

