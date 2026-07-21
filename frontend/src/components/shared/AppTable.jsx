import React, { useMemo, useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import {
  CButton,
  CButtonGroup,
  CCol,
  CFormInput,
  CInputGroup,
  CInputGroupText,
  CRow,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import { cilSearch } from '@coreui/icons'
import CIcon from '@coreui/icons-react'

function DefaultColumnFilter({ column }) {
  const columnFilterValue = column.getFilterValue()

  return (
    <CFormInput
      size="sm"
      type="text"
      value={columnFilterValue ?? ''}
      onChange={(e) => column.setFilterValue(e.target.value)}
      placeholder="Filtrar..."
    />
  )
}

export default function AppTable({
  data = [],
  columns = [],
  searchable = true,
  columnFiltersEnabled = true,
  initialPageSize = 10,
  emptyMessage = 'Nenhum registro encontrado.',
}) {
  const [sorting, setSorting] = useState([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [columnFilters, setColumnFilters] = useState([])

  const defaultColumn = useMemo(
    () => ({
      filterFn: 'includesString',
    }),
    [],
  )

  const table = useReactTable({
    data,
    columns,
    defaultColumn,
    state: {
      sorting,
      globalFilter,
      columnFilters,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onColumnFiltersChange: setColumnFilters,
    globalFilterFn: 'includesString',
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: initialPageSize,
      },
    },
  })

  return (
    <div className="p-3 bg-white rounded shadow-sm">
      <CRow className="mb-3 g-2 align-items-center">
        <CCol md={6}>
          {searchable && (
            <CInputGroup>
              <CInputGroupText>
                <CIcon icon={cilSearch} />
              </CInputGroupText>
              <CFormInput
                placeholder="Pesquisar em toda a tabela..."
                value={globalFilter ?? ''}
                onChange={(e) => setGlobalFilter(e.target.value)}
              />
            </CInputGroup>
          )}
        </CCol>

        <CCol md={6} className="d-flex justify-content-md-end justify-content-start">
          <CFormInput
            type="number"
            min={1}
            max={100}
            style={{ maxWidth: '120px' }}
            value={table.getState().pagination.pageSize}
            onChange={(e) => {
              const value = Number(e.target.value)
              table.setPageSize(value > 0 ? value : 10)
            }}
          />
        </CCol>
      </CRow>

      <div className="table-responsive">
        <CTable hover bordered align="middle">
          <CTableHead color="light">
            {table.getHeaderGroups().map((headerGroup) => (
              <React.Fragment key={headerGroup.id}>
                <CTableRow>
                  {headerGroup.headers.map((header) => {
                    const sorted = header.column.getIsSorted()

                    return (
                      <CTableHeaderCell
                        key={header.id}
                        style={{ width: header.column.columnDef.meta?.width }}
                      >
                        {header.isPlaceholder ? null : (
                          <div
                            onClick={
                              header.column.getCanSort()
                                ? header.column.getToggleSortingHandler()
                                : undefined
                            }
                            style={{
                              cursor: header.column.getCanSort() ? 'pointer' : 'default',
                              userSelect: 'none',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: '8px',
                            }}
                          >
                            <span>
                              {flexRender(header.column.columnDef.header, header.getContext())}
                            </span>

                            <span>{sorted === 'asc' ? '▲' : sorted === 'desc' ? '▼' : '↕'}</span>
                          </div>
                        )}
                      </CTableHeaderCell>
                    )
                  })}
                </CTableRow>

                {columnFiltersEnabled && (
                  <CTableRow>
                    {headerGroup.headers.map((header) => (
                      <CTableHeaderCell key={`${header.id}-filter`}>
                        {header.column.getCanFilter() ? (
                          <DefaultColumnFilter column={header.column} />
                        ) : null}
                      </CTableHeaderCell>
                    ))}
                  </CTableRow>
                )}
              </React.Fragment>
            ))}
          </CTableHead>

          <CTableBody>
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <CTableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <CTableDataCell
                      key={cell.id}
                      style={{ width: cell.column.columnDef.meta?.width }}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </CTableDataCell>
                  ))}
                </CTableRow>
              ))
            ) : (
              <CTableRow>
                <CTableDataCell colSpan={columns.length} className="text-center py-4">
                  {emptyMessage}
                </CTableDataCell>
              </CTableRow>
            )}
          </CTableBody>
        </CTable>
      </div>

      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mt-3">
        <div>
          Página{' '}
          <strong>
            {table.getState().pagination.pageIndex + 1} de {table.getPageCount() || 1}
          </strong>
        </div>

        <CButtonGroup>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            {'<<'}
          </CButton>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Anterior
          </CButton>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Próxima
          </CButton>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          >
            {'>>'}
          </CButton>
        </CButtonGroup>
      </div>
    </div>
  )
}
