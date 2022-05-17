# inheritance tax, gift taxes and estate taxes worldwide
# theoretical effective rates for different estate values

# (c) Dan Neidle of Tax Policy Associates Ltd
# licensed under the GNU General Public License, version 2

# this plots two charts
# first, the effective rate of estate/inheritance/gift tax on estates worth different multiples of average income
# second, the max effective rate found from the above, vs % of GDP collected in tax

# IHT rate and threshold data, and median income data, all from the OECD
# all on basis that estate is being passed by a married couple to their children
# (some countries have different rates for passing to third parties)
# this therefore takes into account any previous spousal exemption

# the OECD data doesn't include the effect of the UK residence nil rate band - I have added it
# undoubtedly there are other special rules/exemptions in other jurisdictions not included in the data

import chart_studio.plotly as py
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
from PIL import Image

# the next line should be uncommented when chart studio is first run - it saves credentials in ~/.plotly
# chart_studio.tools.set_credentials_file(username='taxpolicy', api_key='SECRET')

# alternatively if you just want to display charts locally...
# ... replace py.plot with fig.show (as shown in comments below)

max_estate_size = 100  # x axis max - largest estate size we chart, as multiple of average earnings
estate_resolution = 0.1  # the steps we go up

excel_file = "estate-taxes_worldwide_data.xlsx"

logo_jpg = Image.open("logo_full_white_on_blue.jpg")

all_countries = []
country_max_effective_rate = []
country_estate_tax_of_GDP = []
country_max_statutory_rate = []

# create plotly graph object
# layout settings

logo_layout = [dict(
        source=logo_jpg,
        xref="paper", yref="paper",
        x=1, y=1.03,
        sizex=0.1, sizey=0.1,
        xanchor="right", yanchor="bottom"
    )]

layout = go.Layout(
    images=logo_layout,
    title="Estate value (as multiple of average earnings) vs inheritance/gift/estate tax ETR<br>for children inheriting from two parents",
    xaxis=dict(
        title="Estate value (multiple of average earnings)"
    ),
    yaxis=dict(
        title="Effective rate",
        tickformat=',.0%'  # so we get nice percentages
    ) )

fig = go.Figure(layout=layout)



print(f"Opening {excel_file}")
xl = pd.ExcelFile(excel_file)
print("")
print(f"Opened spreadsheet. Sheets: {xl.sheet_names}")

print("")

df = xl.parse("IHT bands - children")

for country in range (0,len(df)):
    print("")
    print(f"Country: {df.iat[country, 0]}")

    x_data = []  # income multiple
    y_data = []  # effective rate

#   first load bands into a list of dicts
    band = 0
    bands = []
    while not pd.isna(df.iat[country, band * 2 + 5]):   # this keeps going til we hit a NaN
        threshold =  df.iat[country, band * 2 + 5]   # this is % of average earnings
        rate = df.iat[country, band * 2 + 6]
        bands.append({"threshold": threshold, "rate": rate})
        band += 1

    # add a dummy band higher than all estate values - makes algorithm for applying bands cleaner/easier
    bands.append({"threshold": 10000, "rate": df.iat[country, (band-1) * 2 + 6]})

    print(f"bands: {bands}")

    # loop estate values 0 to 50 x average salary, in 0.1 increments
    for estate_value in [estate_value * estate_resolution for estate_value in range(0, int(max_estate_size / estate_resolution) + 1)]:
        total_tax = 0

        if pd.isna(df.iat[country, 2]):
            # no nil rate residence band, i.e. not the UK!
            resi_nil_rate_band = 0
        else:
            resi_nil_rate_band = df.iat[country, 2]
            resi_taper_threshold = df.iat[country, 3]
            resi_taper_fraction = df.iat[country, 4]
            # print(f"This country has a residence nil rate band of {resi_nil_rate_band}, tapering after {resi_taper_threshold} at {resi_taper_fraction}")
            if estate_value > resi_taper_threshold:
                resi_nil_rate_band = max(0, resi_nil_rate_band - resi_taper_fraction * (estate_value - resi_taper_threshold))

        # take account of resi nil rate band, if any
        modified_estate_value = estate_value - resi_nil_rate_band

        for x in range(len(bands)):

            # if we hit the next threshold then apply tax to whole band
            if modified_estate_value >= bands[x+1]["threshold"]:
                total_tax += bands[x]["rate"] * (bands[x+1]["threshold"] - bands[x]["threshold"])  # we reach the next threshold!

            # otherwise apply tax to what's left in this band, then stop looping bands
            else:
                total_tax += bands[x]["rate"] * (modified_estate_value - bands[x]["threshold"])
                break

        ETR = total_tax/estate_value
        print(f"estate value: {round(estate_value, 1)} - effective tax rate {100*ETR}% (residence nil band is {resi_nil_rate_band})")
        x_data.append(round(estate_value,2))
        y_data.append(ETR)

    if bands[x]["rate"] == 0:
        print ("this country has no estate tax at this level - so nothing to plot! (and US will be in this category unless max_estate_size is large)")
        continue

    # add label to last data item showing country (bit hacky; must be better way)
    labels = [""] * (int(max_estate_size / estate_resolution) - 1)
    labels.append(df.iat[country, 0])

    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode="lines+text",    # no markers
        name="Lines and Text",
        text=labels,
        textposition="top center",
        showlegend=False
    ))

    # while we're at it, collate data for second chart
    all_countries.append(df.iat[country, 0])
    country_estate_tax_of_GDP.append(df.iat[country, 1])
    country_max_effective_rate.append(ETR)
    country_max_statutory_rate.append(bands[x]["rate"])

    # now loop to next country



# now create chart of estate value vs effective rate
py.plot(fig, filename = f'IHT_ETR_{max_estate_size}', auto_open=True)

# or for local version, replace the py.plt with:
# fig.show()


# second chart - effective rate vs IHT as % of GDP
layout = go.Layout(
    images=logo_layout,
    title=f"Effective estate/IHT/gift tax rate on estates {max_estate_size}x average earnings, vs tax collected as % of GDP",
    xaxis=dict(
        title="Effective estate/IHT/gift tax rate",
        tickformat=',.0%'  # so we get nice percentages
    ),
    yaxis=dict(
        title="estate/IHT/gift tax collected as % of GDP",
        tickformat='.2%'  # so we get nice percentages
    ))

fig2 = go.Figure(layout=layout)

fig2.add_trace(go.Scatter(
    x=country_max_effective_rate,
    y=country_estate_tax_of_GDP,
    mode="markers+text",  # no markers
    name="markers and Text",
    text=all_countries,
    textposition="top center",
    showlegend=False))

fig2.add_layout_image(
    dict(
        source="www.taxpolicy.org.uk/wp-content/uploads/2022/04/Asset-1@2x-8.png",
        xref="paper", yref="paper",
        x=1, y=1.05,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)


slope, intercept, r_value, p_value, std_err = stats.linregress(country_max_effective_rate, country_estate_tax_of_GDP)
best_fit_y = []

print(f"Slope {slope}, intercept {intercept}, r value{r_value}")

# create data for trendline
for x in country_max_effective_rate:
    best_fit_y.append(intercept + x * slope)

# plot trendline
fig2.add_trace(go.Scatter(
    x=country_max_effective_rate,
    y=best_fit_y,
    mode="lines",
    name="lines",
    showlegend=False))

# now plot it:
py.plot(fig2, filename=f'IHT_ETR_vs_revenue_{max_estate_size}', auto_open=True)

# or for local version, replace the py.plt with:
# fig2.show()



# third chart - maximum rate vs IHT as % of GDP
layout = go.Layout(
    images=logo_layout,
    title=f"Maximum statutory estate/IHT/gift tax rate, vs tax collected as % of GDP",
    xaxis=dict(
        title="Maximum statutory estate/IHT/gift tax rate",
        tickformat=',.0%'  # so we get nice percentages
    ),
    yaxis=dict(
        title="estate/IHT/gift tax collected as % of GDP",
        tickformat='.2%'  # so we get nice percentages
    ))

fig3 = go.Figure(layout=layout)

fig3.add_trace(go.Scatter(
    x=country_max_statutory_rate,
    y=country_estate_tax_of_GDP,
    mode="markers+text",  # no markers
    name="markers and Text",
    text=all_countries,
    textposition="top center",
    showlegend=False))

fig3.add_layout_image(
    dict(
        source="www.taxpolicy.org.uk/wp-content/uploads/2022/04/Asset-1@2x-8.png",
        xref="paper", yref="paper",
        x=0.1, y=0.01,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)


slope, intercept, r_value, p_value, std_err = stats.linregress(country_max_statutory_rate, country_estate_tax_of_GDP)
best_fit_y = []

print(f"Slope {slope}, intercept {intercept}, r value{r_value}")

# create data for trendline
for x in country_max_statutory_rate:
    best_fit_y.append(intercept + x * slope)

# plot trendline
fig3.add_trace(go.Scatter(
    x=country_max_statutory_rate,
    y=best_fit_y,
    mode="lines",
    name="lines",
    showlegend=False))

# now plot it:
py.plot(fig3, filename = 'IHT_statutory_rate_vs_revenue', auto_open=True)

# or for local version, replace the py.plt with:
# fig3.show()


