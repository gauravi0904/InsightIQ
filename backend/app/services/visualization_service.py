import logging
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.schemas.analytics import VisualizationRequest, VisualizationResponse
from backend.app.services.dataset_service import DatasetService

logger = logging.getLogger("insightiq.visualization_service")


class VisualizationService:

    @classmethod
    def generate_chart(cls, dataset_id: int, req: VisualizationRequest, db: Session) -> VisualizationResponse:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        df = DatasetService.load_dataframe(dataset)

        chart_type = req.chart_type.lower()
        x_col = req.x_column
        y_col = req.y_column
        group_col = req.group_column if req.group_column and req.group_column.strip() else None
        title = req.title or f"{req.chart_type.capitalize()} Chart: {x_col}" + (f" vs {y_col}" if y_col else "")

        # 1. Validate column existence
        if x_col not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{x_col}' does not exist in dataset."
            )
        if y_col and y_col not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{y_col}' does not exist in dataset."
            )
        if group_col and group_col not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Grouping column '{group_col}' does not exist in dataset."
            )

        # Helper for type checks
        def is_numeric(c: str) -> bool:
            return pd.api.types.is_numeric_dtype(df[c])

        fig = None

        # 2. Chart type specific validations and generations
        if chart_type == "histogram":
            if not is_numeric(x_col):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Histogram requires a numerical column for X-axis. '{x_col}' is non-numeric ({df[x_col].dtype})."
                )
            fig = px.histogram(
                df, x=x_col, color=group_col,
                title=title, marginal="box",
                template="plotly_white"
            )

        elif chart_type == "scatter":
            if not y_col:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Scatter plot requires both an X-axis and a Y-axis numerical column."
                )
            if not is_numeric(x_col) or not is_numeric(y_col):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Scatter plot requires numerical columns for both axes. Received '{x_col}' ({df[x_col].dtype}) and '{y_col}' ({df[y_col].dtype})."
                )
            fig = px.scatter(
                df, x=x_col, y=y_col, color=group_col,
                title=title, template="plotly_white"
            )

        elif chart_type == "line":
            if not y_col:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Line chart requires a Y-axis numerical column."
                )
            if not is_numeric(y_col):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Line chart requires a numerical column for Y-axis. '{y_col}' is non-numeric ({df[y_col].dtype})."
                )
            # Sort by x if possible
            plot_df = df.copy()
            try:
                plot_df = plot_df.sort_values(by=x_col)
            except Exception:
                pass
            fig = px.line(
                plot_df, x=x_col, y=y_col, color=group_col,
                title=title, template="plotly_white"
            )

        elif chart_type == "bar":
            if y_col and is_numeric(y_col):
                # Aggregated bar
                fig = px.bar(
                    df, x=x_col, y=y_col, color=group_col,
                    title=title, template="plotly_white"
                )
            else:
                # Value counts bar for categorical
                counts_df = df[x_col].value_counts().reset_index()
                counts_df.columns = [x_col, "Count"]
                fig = px.bar(
                    counts_df.head(25), x=x_col, y="Count",
                    title=title or f"Frequency Count: {x_col}",
                    template="plotly_white"
                )

        elif chart_type == "pie":
            # For pie chart, X is the category. If Y is provided, sum Y; otherwise count
            if y_col and is_numeric(y_col):
                agg_df = df.groupby(x_col, as_index=False)[y_col].sum().sort_values(by=y_col, ascending=False).head(15)
                fig = px.pie(
                    agg_df, names=x_col, values=y_col,
                    title=title or f"Distribution of {y_col} by {x_col}",
                    template="plotly_white"
                )
            else:
                counts_df = df[x_col].value_counts().reset_index().head(12)
                counts_df.columns = [x_col, "Count"]
                fig = px.pie(
                    counts_df, names=x_col, values="Count",
                    title=title or f"Category Share: {x_col}",
                    template="plotly_white"
                )

        elif chart_type == "box":
            if not is_numeric(y_col if y_col else x_col):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Box plot requires at least one numerical column. Provided columns are non-numeric."
                )
            if y_col and is_numeric(y_col):
                fig = px.box(
                    df, x=x_col, y=y_col, color=group_col,
                    title=title, template="plotly_white"
                )
            else:
                fig = px.box(
                    df, y=x_col, color=group_col,
                    title=title, template="plotly_white"
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported chart type '{chart_type}'. Choose from: bar, line, histogram, scatter, pie, box."
            )

        fig.update_layout(
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode="closest"
        )

        return VisualizationResponse(
            chart_type=chart_type,
            figure_json=fig.to_json(),
            message="Chart generated successfully."
        )
