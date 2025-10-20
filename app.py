import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import io

from utils.data_processor import DataProcessor
from utils.car_allocator import CarAllocator
from utils.excel_handler import ExcelHandler

def main():
    st.set_page_config(
        page_title="Planowanie Dostaw Materiałów",
        page_icon="🚛",
        layout="wide"
    )
    
    st.title("🚛 Aplikacja do Planowania Dostaw Materiałów")
    st.markdown("**Inteligentna alokacja aut z progresywnym pokrywaniem potrzeb**")
    
    # Initialize session state
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'car_allocation' not in st.session_state:
        st.session_state.car_allocation = None
    
    # File upload section
    st.header("📁 Wczytanie Danych")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tabela1 - Dane zapotrzebowania")
        uploaded_file1 = st.file_uploader(
            "Wybierz plik Excel z danymi zapotrzebowania",
            type=['xlsx', 'xls'],
            key="file1"
        )
        
    with col2:
        st.subheader("Tabela2 - Dostawy w drodze")
        uploaded_file2 = st.file_uploader(
            "Wybierz plik Excel z dostawami w drodze",
            type=['xlsx', 'xls'],
            key="file2"
        )
    
    # Process data when both files are uploaded
    if uploaded_file1 and uploaded_file2:
        try:
            with st.spinner("Przetwarzanie danych..."):
                # Load and process data
                excel_handler = ExcelHandler()
                data_processor = DataProcessor()
                
                # Read Excel files
                tabela1_data = excel_handler.read_excel_file(uploaded_file1, "Tabela1")
                tabela2_data = excel_handler.read_excel_file(uploaded_file2, "Tabela2")
                
                # Process data
                processed_data = data_processor.process_data(tabela1_data, tabela2_data)
                st.session_state.processed_data = processed_data
                
            st.success("✅ Dane zostały pomyślnie przetworzone!")
            
            # Display processed data summary
            display_data_summary(processed_data)
            
            # Interactive controls
            display_interactive_controls()
            
        except Exception as e:
            st.error(f"❌ Błąd podczas przetwarzania danych: {str(e)}")
            st.exception(e)

def display_data_summary(processed_data):
    """Display summary of processed data"""
    st.header("📊 Podsumowanie Danych")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_demand = processed_data['Potrzeba_netto'].sum()
        st.metric("Całkowita potrzeba netto", f"{total_demand:,.0f} kg")
    
    with col2:
        total_deliveries = processed_data['W_drodze'].sum()
        st.metric("Dostawy w drodze", f"{total_deliveries:,.0f} kg")
    
    with col3:
        unique_batches = processed_data['Batch'].nunique()
        st.metric("Liczba partii", unique_batches)
    
    with col4:
        total_cartons = processed_data['Kartony_zaokr'].sum()
        st.metric("Kartony do zamówienia", f"{total_cartons:,.0f}")
    
    # Show detailed data
    if st.checkbox("Pokaż szczegółowe dane"):
        st.subheader("Szczegółowe dane potrzeb")
        
        # Format data for display
        display_data = processed_data.copy()
        display_data['Requirement Date'] = pd.to_datetime(display_data['Requirement Date']).dt.strftime('%Y-%m-%d')
        
        numeric_cols = ['Net Demand', 'W_drodze', 'Potrzeba_netto', 'Conv', 'Kartony_zaokr']
        for col in numeric_cols:
            if col in display_data.columns:
                display_data[col] = display_data[col].round(2)
        
        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

def display_interactive_controls():
    """Display interactive controls for car allocation"""
    if st.session_state.processed_data is None:
        return
    
    st.header("🚗 Interaktywna Alokacja Aut")
    
    processed_data = st.session_state.processed_data
    
    # Date range for coverage
    min_date = processed_data['Requirement Date'].min()
    max_date = processed_data['Requirement Date'].max()
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_date = st.date_input(
            "Data docelowa pokrycia potrzeb",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="target_date"
        )
    
    with col2:
        num_cars = st.number_input(
            "Liczba aut do wysłania",
            min_value=1,
            max_value=50,
            value=5,
            key="num_cars"
        )
    
    # Car capacity setting
    car_capacity = st.slider(
        "Pojemność auta (kartony)",
        min_value=50,
        max_value=200,
        value=105,
        key="car_capacity"
    )
    
    # Allocation button
    if st.button("🚀 Przeprowadź Alokację Aut", type="primary"):
        try:
            with st.spinner("Przeprowadzanie inteligentnej alokacji..."):
                car_allocator = CarAllocator()
                allocation_result = car_allocator.allocate_cars(
                    processed_data,
                    target_date,
                    num_cars,
                    car_capacity
                )
                st.session_state.car_allocation = allocation_result
                
            st.success("✅ Alokacja aut została zakończona!")
            
            # Display results
            display_allocation_results()
            
        except Exception as e:
            st.error(f"❌ Błąd podczas alokacji aut: {str(e)}")
    
    # Display existing allocation if available
    if st.session_state.car_allocation:
        display_allocation_results()

def display_allocation_results():
    """Display car allocation results and visualization"""
    if not st.session_state.car_allocation:
        return
    
    allocation_result = st.session_state.car_allocation
    
    st.header("📋 Wyniki Alokacji")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_allocated = allocation_result['car_orders']['Kartony'].sum()
        st.metric("Przydzielone kartony", f"{total_allocated:,.0f}")
    
    with col2:
        total_weight = allocation_result['car_orders']['Suma_netto_kg'].sum()
        st.metric("Całkowita waga", f"{total_weight:,.0f} kg")
    
    with col3:
        cars_used = allocation_result['car_orders']['Numer_auta'].nunique()
        st.metric("Wykorzystane auta", cars_used)
    
    with col4:
        coverage_pct = (total_allocated / st.session_state.processed_data['Kartony_zaokr'].sum()) * 100
        st.metric("Pokrycie potrzeb", f"{coverage_pct:.1f}%")
    
    # Car orders table
    st.subheader("🚛 Lista Zamówień dla Aut (Zagregowane)")
    
    car_orders = allocation_result['car_orders'].copy()
    
    # Reorder columns for better display
    column_order = ['Numer_auta', 'Batch', 'Material', 'Leaf', 'Kartony', 'Conv', 'Suma_netto_kg']
    car_orders = car_orders[column_order]
    
    st.info(f"📊 Całkowita liczba pozycji w zamówieniu: **{len(car_orders)}** pozycji (bez rozbicia na daty)")
    
    st.dataframe(
        car_orders,
        use_container_width=True,
        hide_index=True
    )
    
    # Coverage visualization
    st.subheader("📈 Wizualizacja Pokrycia Potrzeb")
    
    # Before/after coverage chart
    coverage_data = allocation_result['coverage_analysis']
    
    fig = go.Figure()
    
    # Before allocation
    fig.add_trace(go.Scatter(
        x=coverage_data['Requirement Date'],
        y=coverage_data['Potrzeba_przed'],
        mode='lines+markers',
        name='Potrzeba przed alokacją',
        line=dict(color='red', width=2)
    ))
    
    # After allocation
    fig.add_trace(go.Scatter(
        x=coverage_data['Requirement Date'],
        y=coverage_data['Potrzeba_po'],
        mode='lines+markers',
        name='Potrzeba po alokacji',
        line=dict(color='green', width=2),
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.2)'
    ))
    
    fig.update_layout(
        title='Pokrycie Potrzeb w Czasie',
        xaxis_title='Data',
        yaxis_title='Potrzeba (kartony)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="coverage_chart")
    
    # Material distribution pie chart
    st.subheader("🥧 Rozkład Materiałów w Autach")
    
    # Filter out NaN materials before grouping
    valid_materials = car_orders[car_orders['Material'].notna()].copy()
    
    if not valid_materials.empty:
        material_summary = valid_materials.groupby('Material')['Kartony'].sum().reset_index()
        
        fig_pie = px.pie(
            material_summary,
            values='Kartony',
            names='Material',
            title='Rozkład materiałów (kartony)'
        )
        
        st.plotly_chart(fig_pie, use_container_width=True, key="material_pie_chart")
    else:
        st.info("Brak danych materiałowych do wyświetlenia")
    
    # Export functionality
    st.subheader("💾 Export Wyników")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Eksportuj do Excel"):
            excel_data = create_excel_export(allocation_result)
            st.download_button(
                label="⬇️ Pobierz plik Excel",
                data=excel_data,
                file_name=f"alokacja_aut_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📋 Eksportuj zamówienia CSV"):
            csv_data = car_orders.to_csv(index=False)
            st.download_button(
                label="⬇️ Pobierz CSV",
                data=csv_data,
                file_name=f"zamowienia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

def create_excel_export(allocation_result):
    """Create Excel file with allocation results"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Car orders sheet
        allocation_result['car_orders'].to_excel(
            writer, 
            sheet_name='Zamówienia_Aut',
            index=False
        )
        
        # Coverage analysis sheet
        allocation_result['coverage_analysis'].to_excel(
            writer, 
            sheet_name='Analiza_Pokrycia',
            index=False
        )
        
        # Summary sheet
        summary_data = {
            'Metryka': [
                'Całkowita liczba kartonów',
                'Całkowita waga (kg)',
                'Liczba użytych aut',
                'Średnia liczba kartonów na auto',
                'Data docelowa pokrycia'
            ],
            'Wartość': [
                allocation_result['car_orders']['Kartony'].sum(),
                allocation_result['car_orders']['Suma_netto_kg'].sum(),
                allocation_result['car_orders']['Numer_auta'].nunique(),
                allocation_result['car_orders']['Kartony'].sum() / allocation_result['car_orders']['Numer_auta'].nunique(),
                allocation_result['target_date']
            ]
        }
        
        pd.DataFrame(summary_data).to_excel(
            writer,
            sheet_name='Podsumowanie',
            index=False
        )
    
    output.seek(0)
    return output.getvalue()

if __name__ == "__main__":
    main()
