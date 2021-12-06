'''

Name: ---
CS230: ---
Data: ---
URL: Link to your web application online
Description:

This program uses a list of 100 skyscrapers which a user on a created website can filter and always see in form of a table. The user can select between a map and different graphs to visualize the selected data. A 3D map of skyscrapers in New York City is also available. It shows the relative heights of the buidlings to each other.

'''

import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import os
import webbrowser
import folium
import pydeck as pdk #For extra credit. Source see in code.

def website(): #def website(): represents main function
    st.set_page_config(page_title = "CS230.5 Skyscrapers2021", page_icon = "Bentley_Logo_Shield_Only_Blue.png", layout = "wide", initial_sidebar_state = "auto", menu_items = {"About": "---"}) #Source: https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config

    #First defining and calling functions
    def openfile():
        global df_skyscrapers
        df_skyscrapers = pd.read_csv('Skyscrapers2021.csv')
        global columns
        columns = list(df_skyscrapers.columns)
        global names
        names = list(df_skyscrapers["NAME"])
        global cities
        cities = list(df_skyscrapers["CITY"])
        global completions
        completions = list(df_skyscrapers["COMPLETION"])
        global meters
        meters = list(df_skyscrapers["Meters"])
        global feet
        feet = list(df_skyscrapers["Feet"])
        global floors
        floors = list(df_skyscrapers["FLOORS"])
        global materials
        materials = list(df_skyscrapers["MATERIAL"])
        global functions
        functions = list(df_skyscrapers["FUNCTION"])
    openfile()

    def unique_lists(): #Define to allow user to filter only unique data
        global cities_unique
        cities_unique = []
        for i in cities:
            if i not in cities_unique:
                cities_unique.append(i)
        global materials_unique
        materials_unique = []
        for i in materials:
            if "/" in i:
                materials_split = i.split("/")
                for j in materials_split:
                    if j.capitalize() not in materials_unique:
                        materials_unique.append(j.capitalize())
            else:
                if i.capitalize() not in materials_unique:
                        materials_unique.append(i.capitalize())
        global functions_unique
        functions_unique = []
        for i in functions:
            if " / " in i:
                functions_split = i.split(" / ")
                for j in functions_split:
                    if j.lower().capitalize() not in functions_unique:
                        functions_unique.append(j.lower().capitalize())
            else:
                if i.lower().capitalize() not in functions_unique:
                    materials_unique.append(i.lower().capitalize())
    unique_lists()

    def sidebar():
        st.sidebar.title("Filters & Selections")

        st.sidebar.header("Selections") #Selections that influence visualization
        global measuring_unit
        measuring_unit = st.sidebar.radio("Select measuring unit", ["Feet", "Meters"])
        global visualization_tool
        visualization_tool = st.sidebar.radio("Select visualization tool", ["N/A", "3D Map of NYC", "Graphs", "Map"])
        if visualization_tool == "Graphs":
            global graph_style
            graph_style = st.sidebar.radio("Select type of graph", ["Bar chart", "Pie chart"])
        elif visualization_tool == "Map":
            global map_style
            cities_unique.insert(0, "World")
            map_style = st.sidebar.multiselect("Select map of...", cities_unique)

        st.sidebar.header("Filters") #Selections that influence dataframe
        global names_filtered
        names.sort()
        names_filtered = st.sidebar.multiselect("Select unique buildings", names)
        global cities_filtered
        cities_unique.sort()
        cities_filtered = st.sidebar.multiselect("Select buidlings in...", cities_unique)
        global completions_filtered
        completions_filtered = st.sidebar.slider("Select buildings built after/in...", min(completions), max(completions))
        if measuring_unit == "Meters":
            global meters_filtered
            meters_stripped = [float(i.replace(" m", "")) for i in meters]
            meters_filtered = st.sidebar.slider("Select buildings higher than/equal to ... meters", min(meters_stripped), max(meters_stripped))
        else:
            global feet_filtered
            feet_stripped = [int(i.replace(",", "").replace(" ft", "")) for i in feet]
            feet_filtered = st.sidebar.slider("Select buildings higher than/equal to ... feet", min(feet_stripped), max(feet_stripped))
        global floors_filtered
        floors_filtered = st.sidebar.slider("Select buildings with more than/equal to ... floors", int(min(floors)), int(max(floors)))
        global materials_filtered
        materials_unique.sort()
        materials_filtered = st.sidebar.multiselect("Select buildings made out of...", materials_unique)
        global functions_filtered
        functions_unique.sort()
        functions_filtered = st.sidebar.multiselect("Select buildings used for...", functions_unique)

        st.sidebar.header("Display") #Selections that influence how dataframe is displayed
        st.sidebar.write("Select which columns to show and up to two columns to sort the filtered buildings and choose ascending/descending order")
        global columns_filtered #need multiple lists for the different selections (e.g., cannot include NAME when selecting columns, as names should always be diplayed by default, but user should choose NAME to sort dataframe)
        columns_print = [i.lower().capitalize() for i in columns]
        columns_print_filter = list(columns_print)
        columns_print_filter.pop(1)
        columns_print.sort()
        columns_print_filter.sort()
        columns_filtered = st.sidebar.multiselect("Select which data to show in the order you prefer (Name is always displayed)", columns_print_filter)
        col1, col2 = st.sidebar.columns((1, 1))
        with col1:
            if columns_filtered == []:
                columns_filtered_print = list(columns_print)
                columns_filtered_print.insert(0, "N/A")
            else:
                columns_filtered_print = list(columns_filtered)
                columns_filtered_print.insert(0, "Name")
                columns_filtered_print.sort()
                columns_filtered_print.insert(0, "N/A")
            global order_columns_1
            order_columns_1 = st.selectbox("Select first column", columns_filtered_print)
            global order_columns_2
            order_columns_2 = st.selectbox("Select second column", columns_filtered_print)
        with col2:
            global order_1
            order_1 = st.radio("Select order for first column", ["Ascending", "Descending"])
            global order_2
            order_2 = st.radio("Select order for second column", ["Ascending", "Descending"])
        if order_columns_2 != "N/A":
            if order_columns_1 == order_columns_2:
                st.sidebar.warning("Do not select the same column twice.")
    sidebar()

    def dataframe(df_input = df_skyscrapers):
        if names_filtered == []: #First setting defaults (when no filter selected, entire list used by default)
            names_filtered_applied = names
        else:
            names_filtered_applied = names_filtered
        if cities_filtered == []:
            cities_filtered_applied = cities_unique
        else:
            cities_filtered_applied = cities_filtered
        if materials_filtered == []:
            rows_materials = materials
        else:
            rows_materials = []
            for i in materials_filtered:
                for j in range(len(df_input)):
                    if i.lower() in df_input.at[j, "MATERIAL"]:
                        if df_input.at[j, "MATERIAL"] not in rows_materials:
                            rows_materials.append(df_input.at[j, "MATERIAL"])
        if functions_filtered == []:
            rows_functions = functions
        else:
            rows_functions = []
            for i in functions_filtered:
                for j in range(len(df_input)):
                    if i.lower() in df_input.at[j, "FUNCTION"] or i.upper() in df_input.at[j, "FUNCTION"]:
                        if df_input.at[j, "FUNCTION"] not in rows_functions:
                            rows_functions.append(df_input.at[j, "FUNCTION"])

        if measuring_unit == "Meters": #Special case for 3D Map of NYC, as filters should not impact visualization, and only NYC buidlings should be displayed
            if visualization_tool == "3D Map of NYC":
                df_output = df_input.loc[(df_input["CITY"].isin(["New York City"]))]
            else:
                df_output = df_input.loc[(df_input["NAME"].isin(names_filtered_applied)) & (df_input["CITY"].isin(cities_filtered_applied)) & (df_input["COMPLETION"] >= completions_filtered) & (df_input["FLOORS"] >= floors_filtered) & (df_input["Meters"].str.replace(" m", "").astype(float) >= meters_filtered) & (df_input["MATERIAL"].isin(rows_materials)) & (df_input["FUNCTION"].isin(rows_functions))] #source for .astype(): https://www.geeksforgeeks.org/python-pandas-series-astype-to-convert-data-type-of-series/
        else:
            if visualization_tool == "3D Map of NYC":
                df_output = df_input.loc[(df_input["CITY"].isin(["New York City"]))]
            else:
                df_output = df_input.loc[(df_input["NAME"].isin(names_filtered_applied)) & (df_input["CITY"].isin(cities_filtered_applied)) & (df_input["COMPLETION"] >= completions_filtered) & (df_input["FLOORS"] >= floors_filtered) & (df_input["Feet"].str.replace(",", "").str.replace(" ft", "").astype(int) >= feet_filtered) & (df_input["MATERIAL"].isin(rows_materials)) & (df_input["FUNCTION"].isin(rows_functions))] #source for .astype(): https://www.geeksforgeeks.org/python-pandas-series-astype-to-convert-data-type-of-series/

        if columns_filtered != []: #choose columns to display, order of choice matters
            columns_input = []
            for i in columns_filtered:
                for j in columns:
                    if i.upper() in j:
                        columns_input.append(j)
                    elif i.capitalize() in j:
                        columns_input.append(j)
            columns_input.insert(0, "NAME")
            df_output = df_output.loc[:, columns_input]

        global df_dict #dict later used for visualization
        df_dict = {}
        output_names = [i.NAME for i in df_output.itertuples()]
        for i in df_input.itertuples():
            if i.NAME in output_names:
                df_dict[i.NAME] = [i.CITY, i.COMPLETION, float(i.Meters.replace(" m", "")), int(i.Feet.replace(",", "").replace(" ft", "")), i.MATERIAL, i.FUNCTION, i.Link, i.Latitude, i.Longitude]

        if order_columns_1 != "N/A" and order_columns_2 == "N/A": #sort dataframe by up to two columns
            for i in columns:
                if order_columns_1.upper() == i:
                    if order_1 == "Ascending":
                        df_output = df_output.sort_values(order_columns_1.upper(), ascending = True)
                    else:
                        df_output = df_output.sort_values(order_columns_1.upper(), ascending = False)
                if order_columns_1.capitalize() == i:
                    if order_1 == "Ascending":
                        df_output = df_output.sort_values(order_columns_1.capitalize(), ascending = True)
                    else:
                        df_output = df_output.sort_values(order_columns_1.capitalize(), ascending = False)
        elif order_columns_1 != "N/A" and order_columns_2 != "N/A":
            for i in columns:
                if order_columns_1.upper() == i:
                    for j in columns:
                        if order_columns_2.upper() == j:
                            if order_1 == "Ascending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.upper()], ascending = [True, True])
                            elif order_1 == "Descending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.upper()], ascending = [False, True])
                            elif order_1 == "Ascending" and order_2 == "Descending":
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.upper()], ascending = [True, False])
                            else:
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.upper()], ascending = [False, False])
                        if order_columns_2.capitalize() == j:
                            if order_1 == "Ascending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.capitalize()], ascending = [True, True])
                            elif order_1 == "Descending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.capitalize()], ascending = [False, True])
                            elif order_1 == "Ascending" and order_2 == "Descending":
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.capitalize()], ascending = [True, False])
                            else:
                                df_output = df_output.sort_values(by = [order_columns_1.upper(), order_columns_2.capitalize()], ascending = [False, False])
                if order_columns_1.capitalize() == i:
                    for j in columns:
                        if order_columns_2.upper() == j:
                            if order_1 == "Ascending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.upper()], ascending = [True, True])
                            elif order_1 == "Descending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.upper()], ascending = [False, True])
                            elif order_1 == "Ascending" and order_2 == "Descending":
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.upper()], ascending = [True, False])
                            else:
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.upper()], ascending = [False, False])
                        if order_columns_2.capitalize() == j:
                            if order_1 == "Ascending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.capitalize()], ascending = [True, True])
                            elif order_1 == "Descending" and order_2 == "Ascending":
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.capitalize()], ascending = [False, True])
                            elif order_1 == "Ascending" and order_2 == "Descending":
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.capitalize()], ascending = [True, False])
                            else:
                                df_output = df_output.sort_values(by = [order_columns_1.capitalize(), order_columns_2.capitalize()], ascending = [False, False])
        return df_output
    dataframe()

    def graphs(): #First program labels/ data to be used in different charts
        st.write("Below the data is visualized as bar charts. Customize which charts to see here:")
        col1, col2, col3 = st.columns((1, 1, 1))
        with col1:
            chart_labels = st.selectbox("Select labels", ["City", "Completion", "Function", "Material"])
        with col2:
            chart_measure = st.selectbox(f"Select to see total number of buildings or total accumulated height per {chart_labels.lower()}", ["Accumulated height", "Number of buildings"])
        with col3:
            if graph_style == "Bar chart":
                chart_color = st.color_picker("Select the graph's color by clicking on the colored box", "#0075be") #Use Bentley's color code, Source: https://docs.streamlit.io/library/api-reference/widgets/st.color_picker

        axis = {}
        y_axis = []
        if chart_labels == "City":
            for i in df_dict:
                if df_dict[i][0] not in axis.keys():
                    axis[df_dict[i][0]] = [1, df_dict[i][3], df_dict[i][2]]
                else:
                    axis[df_dict[i][0]][0] = axis[df_dict[i][0]][0] + 1
                    axis[df_dict[i][0]][1] = axis[df_dict[i][0]][1] + df_dict[i][3]
                    axis[df_dict[i][0]][2] = axis[df_dict[i][0]][2] + df_dict[i][2]
            x_axis = axis.keys()
            for i in axis:
                if chart_measure == "Number of buildings":
                    y_axis.append(int(axis[i][0]))
                else:
                    if measuring_unit == "Feet":
                        y_axis.append(int(axis[i][1]))
                    else:
                        y_axis.append(axis[i][2])
        elif chart_labels == "Completion":
            for i in df_dict:
                if df_dict[i][1] not in axis.keys():
                    axis[df_dict[i][1]] = [1, df_dict[i][3], df_dict[i][2]]
                else:
                    axis[df_dict[i][1]][0] = axis[df_dict[i][1]][0] + 1
                    axis[df_dict[i][1]][1] = axis[df_dict[i][1]][1] + df_dict[i][3]
                    axis[df_dict[i][1]][2] = axis[df_dict[i][1]][2] + df_dict[i][2]
            x_axis = axis.keys()
            for i in axis:
                if chart_measure == "Number of buildings":
                    y_axis.append(int(axis[i][0]))
                else:
                    if measuring_unit == "Feet":
                        y_axis.append(int(axis[i][1]))
                    else:
                        y_axis.append(axis[i][2])
        elif chart_labels == "Function":
            for i in df_dict:
                i_split = df_dict[i][5].split(" / ")
                for j in i_split:
                    if j not in axis.keys():
                        axis[j] = [1, df_dict[i][3], df_dict[i][2]]
                    else:
                        axis[j][0] = axis[j][0] + 1
                        axis[j][1] = axis[j][1] + df_dict[i][3]
                        axis[j][2] = axis[j][2] + df_dict[i][2]
            x_axis = [i.lower().capitalize() for i in axis.keys()]
            for i in axis:
                if chart_measure == "Number of buildings":
                    y_axis.append(int(axis[i][0]))
                else:
                    if measuring_unit == "Feet":
                        y_axis.append(int(axis[i][1]))
                    else:
                        y_axis.append(axis[i][2])
        else:
            for i in df_dict:
                i_split = df_dict[i][4].split("/")
                for j in i_split:
                    if j not in axis.keys():
                        axis[j] = [1, df_dict[i][3], df_dict[i][2]]
                    else:
                        axis[j][0] = axis[j][0] + 1
                        axis[j][1] = axis[j][1] + df_dict[i][3]
                        axis[j][2] = axis[j][2] + df_dict[i][2]
            x_axis = [i.lower().capitalize() for i in axis.keys()]
            for i in axis:
                if chart_measure == "Number of buildings":
                    y_axis.append(int(axis[i][0]))
                else:
                    if measuring_unit == "Feet":
                        y_axis.append(int(axis[i][1]))
                    else:
                        y_axis.append(axis[i][2])

        if graph_style == "Bar chart": #Second code graphs
            fig, ax = plt.subplots()
            ax.bar(x_axis, y_axis, color = chart_color) #Source for labelling axes: https://www.programcreek.com/python/example/114095/streamlit.pyplot
            if chart_labels == "City":
                ax.set_xlabel("City")
            elif chart_labels == "Completion":
                ax.set_xlabel("Completion")
            elif chart_labels == "Function":
                ax.set_xlabel("Function")
            else:
                ax.set_xlabel("Material")
            if chart_measure == "Number of buildings":
                ax.set_ylabel("Buildings")
            else:
                if measuring_unit == "Feet":
                    ax.set_ylabel("Feet")
                else:
                    ax.set_ylabel("Meters")
            st.pyplot(fig)
        else:
            y_axis_pie = [round(i) for i in y_axis]
            fig, ax = plt.subplots()
            ax.pie(y_axis_pie, labels = x_axis, autopct = '%.1f%%')
            st.pyplot(fig)

    def maps(placelist = df_dict): #Code map of the world. User can zoom in to see unqiue cities.
        center = [40.52, 34.34]
        worldmap = folium.Map(location = center, zoom_start = 2)

        for i in placelist:
            lat = placelist[i][-2]
            lon = placelist[i][-1]

            icon = folium.Icon(icon = 'building', prefix="fa", color = 'blue')
            folium.Marker(location = [lat, lon], popup = '<a href=\"' + placelist[i][-3] + '\">' + placelist[i][-3] + '</a>', tooltip = i, icon = icon).add_to(worldmap)

        filePath = os.getcwd() + "\\worldmap.html"
        worldmap.save(filePath)
        webbrowser.open('file://' + filePath)

    def NYC_map(): #Source: https://deckgl.readthedocs.io/en/latest/gallery/grid_layer.html, https://docs.streamlit.io/library/api-reference/charts/st.pydeck_chart
        df_nyc = df_skyscrapers.loc[df_skyscrapers["CITY"].isin(["New York City"]), ["NAME", "Latitude", "Longitude", "Feet", "Meters"]]
        x = 0
        for i in df_nyc.itertuples(): #Pydeck creates columns which should represent the relative height of the buidlings. Columns increase for everytime the same location is in the dataframe. So adjust dataframe to include the same building as often as its is feet/meters high. Tooltip will show actual height. Names cannot be included in the tooltip, as pydeck/streamlit does not allow to.
            counter = 1
            if measuring_unit == "Feet":
                if i.Feet != 0:
                    x += 3000 #3000 to ensure index of new row is not already in df_nyc, as 3000 > max(i.Feet)
                    while counter < int(i.Feet.replace(",", "").replace(" ft", "")):
                        df_nyc.loc[x] = [i.NAME, i.Latitude, i.Longitude, 0, 0] #Add rows to dataframe
                        counter += 1
                        x += 1
            if measuring_unit == "Meters":
                if i.Meters != 0:
                    x += 600
                    while counter < float(i.Meters.replace(" m", "")):
                        df_nyc.loc[x] = [i.NAME, i.Latitude, i.Longitude, 0, 0]
                        counter += 1
                        x += 1

        layer = pdk.Layer("GridLayer", data = df_nyc, get_position = "[Longitude, Latitude]",radius = 150, pickable = True, extruded = True, cell_size = 200, elevation_scale = 4)
        view_state = pdk.ViewState(latitude = 40.736254, longitude = -73.999, zoom = 11, bearing = 0, pitch = 45)
        if measuring_unit == "Feet":
            tooltip = {"html": "<b>Height:</b> {count} ft",  "style": {"backgroundColor": "#0075be", "color": "#b3c4cc"}} #Source: https://github.com/visgl/deck.gl/issues/4917
            st.pydeck_chart(pdk.Deck(layers = [layer], initial_view_state = view_state, tooltip = tooltip,))
        else:
            tooltip = {"html": "<b>Height:</b> {count} m",  "style": {"backgroundColor": "#0075be", "color": "#b3c4cc"}} #Using Bentley's color code
            st.pydeck_chart(pdk.Deck(layers = [layer], initial_view_state = view_state, tooltip = tooltip,))

    #Second coding website
    col1, col2 = st.columns((5, 1)) #Source: https://docs.streamlit.io/library/api-reference/layout/st.columns
    with col1:
        st.title("Skyscrapers 2021")
    with col2:
        st.image("Bentley_Logo_Shield_Only_Blue.png", width = 70)
    st.markdown("Welcome to this website! A list of the **100 largest skyscrapers** of the world is provided for you. There are many possibilities to filter the list. You can always see the current selection in the table right below this text. You can visualize the data with graphs and maps.") #Source: https://docs.streamlit.io/library/api-reference/text/st.markdown
    with st.expander("Open/close this expander to unhide/hide the table of selected skyscrapers", expanded = True): #Source: https://docs.streamlit.io/library/api-reference/layout/st.expander
        st.dataframe(dataframe())
    st.header("Visualization")
    if visualization_tool == "N/A":
        st.warning("Currently no visualization is applied. Select one in the sidebar.") #Source: https://docs.streamlit.io/library/api-reference/status/st.warning
    elif visualization_tool == "Graphs":
       graphs()
    elif visualization_tool == "Map":
        st.write("This visualization opens a new tab in your browser displaying a map with the selected skyscrapers. Press the button below to open the map or reopen it when new filters are applied.")
        map_button = st.button("Open map") #Source: https://docs.streamlit.io/library/api-reference/widgets/st.button
        if map_button == True:
            st.balloons() #Easteregg
            maps()
    else:
        if measuring_unit == "Feet":
            st.markdown("Here you can see a map of New York City and its skyscrapers that are part of the provided list. Applying filters **does not** impact this visualization. You may only change the display.")
        else:
            st.markdown("Here you can see a map of New York City and its skyscrapers that are part of the provided list. Applying filters **does not** impact this visualization. You may only change the display. Height in Meters is rounded up. See table for precise height.")
        NYC_map()

website()
