import React from 'react'

function DataTable({ table }) {
  if (!table || !table.data) return null

  // For now, just display as text since we're passing text format
  return (
    <div className="data-table">
      <pre className="table-content">
        {table.data}
      </pre>
    </div>
  )
}

export default DataTable

