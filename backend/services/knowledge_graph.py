"""
Knowledge Graph Manager for the AI Math Tutor system.
Manages knowledge nodes and their relationships.
"""
import json
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.models.knowledge import KnowledgeNode, KnowledgeRelation


class KnowledgeGraphManager:
    """
    Manager class for knowledge graph operations.
    Handles CRUD operations for knowledge nodes and relations.
    """

    def __init__(self, db: Session):
        """
        Initialize the Knowledge Graph Manager.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """
        Get a knowledge node by ID.
        
        Args:
            node_id: The unique identifier of the node
            
        Returns:
            KnowledgeNode if found, None otherwise
        """
        return self.db.query(KnowledgeNode).filter(
            KnowledgeNode.id == node_id
        ).first()

    def get_related_nodes(
        self,
        node_id: str,
        relation_types: Optional[List[str]] = None
    ) -> List[KnowledgeNode]:
        """
        Get all nodes related to the given node.
        
        Args:
            node_id: The ID of the source node
            relation_types: Optional list of relation types to filter by
                          (e.g., ['PREREQUISITE', 'RELATED', 'EXTENDS', 'SIMILAR'])
        
        Returns:
            List of related KnowledgeNode objects
        """
        query = self.db.query(KnowledgeRelation).filter(
            KnowledgeRelation.from_id == node_id
        )
        
        if relation_types:
            query = query.filter(KnowledgeRelation.relation_type.in_(relation_types))
        
        relations = query.all()
        
        related_node_ids = [rel.to_id for rel in relations]
        
        if not related_node_ids:
            return []
        
        return self.db.query(KnowledgeNode).filter(
            KnowledgeNode.id.in_(related_node_ids)
        ).all()


    def add_node(self, node: KnowledgeNode) -> KnowledgeNode:
        """
        Add a new knowledge node to the graph.
        
        Args:
            node: The KnowledgeNode to add
            
        Returns:
            The added KnowledgeNode with generated ID if not provided
        """
        if not node.id:
            node.id = str(uuid.uuid4())
        
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def add_relation(self, relation: KnowledgeRelation) -> KnowledgeRelation:
        """
        Add a new relation between knowledge nodes.
        
        Args:
            relation: The KnowledgeRelation to add
            
        Returns:
            The added KnowledgeRelation
            
        Raises:
            ValueError: If either from_node or to_node doesn't exist
        """
        # Verify both nodes exist
        from_node = self.get_node(relation.from_id)
        to_node = self.get_node(relation.to_id)
        
        if not from_node:
            raise ValueError(f"Source node with ID '{relation.from_id}' not found")
        if not to_node:
            raise ValueError(f"Target node with ID '{relation.to_id}' not found")
        
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return relation

    def get_all_nodes(
        self,
        subject: Optional[str] = None,
        unit: Optional[str] = None
    ) -> List[KnowledgeNode]:
        """
        Get all knowledge nodes, optionally filtered by subject and unit.
        
        Args:
            subject: Optional subject filter
            unit: Optional unit filter
            
        Returns:
            List of KnowledgeNode objects
        """
        query = self.db.query(KnowledgeNode)
        
        if subject:
            query = query.filter(KnowledgeNode.subject == subject)
        if unit:
            query = query.filter(KnowledgeNode.unit == unit)
        
        return query.all()

    def get_node_relations(self, node_id: str) -> List[KnowledgeRelation]:
        """
        Get all relations where the given node is the source.
        
        Args:
            node_id: The ID of the source node
            
        Returns:
            List of KnowledgeRelation objects
        """
        return self.db.query(KnowledgeRelation).filter(
            KnowledgeRelation.from_id == node_id
        ).all()

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a knowledge node and its relations.
        
        Args:
            node_id: The ID of the node to delete
            
        Returns:
            True if deleted, False if node not found
        """
        node = self.get_node(node_id)
        if not node:
            return False
        
        # Delete related relations
        self.db.query(KnowledgeRelation).filter(
            (KnowledgeRelation.from_id == node_id) |
            (KnowledgeRelation.to_id == node_id)
        ).delete(synchronize_session=False)
        
        self.db.delete(node)
        self.db.commit()
        return True

    def delete_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: str
    ) -> bool:
        """
        Delete a specific relation.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            relation_type: Type of relation
            
        Returns:
            True if deleted, False if relation not found
        """
        result = self.db.query(KnowledgeRelation).filter(
            KnowledgeRelation.from_id == from_id,
            KnowledgeRelation.to_id == to_id,
            KnowledgeRelation.relation_type == relation_type
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return result > 0

    def export_knowledge_graph(self) -> str:
        """
        Export the entire knowledge graph to JSON format.
        
        Exports all nodes and relations in a structured JSON format
        that can be used for backup and restoration.
        
        Returns:
            JSON string containing all nodes and relations
            
        Requirements: 13.4
        """
        # Get all nodes
        nodes = self.db.query(KnowledgeNode).all()
        
        # Get all relations
        relations = self.db.query(KnowledgeRelation).all()
        
        # Convert nodes to dictionaries
        nodes_data = []
        for node in nodes:
            node_dict = {
                "id": node.id,
                "name": node.name,
                "subject": node.subject,
                "unit": node.unit,
                "difficulty": node.difficulty,
                "description": node.description,
                "created_at": node.created_at.isoformat() if node.created_at else None
            }
            nodes_data.append(node_dict)
        
        # Convert relations to dictionaries
        relations_data = []
        for relation in relations:
            relation_dict = {
                "from_id": relation.from_id,
                "to_id": relation.to_id,
                "relation_type": relation.relation_type,
                "weight": relation.weight
            }
            relations_data.append(relation_dict)
        
        # Create the export structure
        export_data = {
            "version": "1.0",
            "nodes": nodes_data,
            "relations": relations_data
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)

    def import_knowledge_graph(self, json_data: str, clear_existing: bool = False) -> Dict[str, Any]:
        """
        Import knowledge graph data from JSON format.
        
        Args:
            json_data: JSON string containing nodes and relations
            clear_existing: If True, clear existing data before import
            
        Returns:
            Dictionary with import statistics:
            - nodes_imported: Number of nodes imported
            - relations_imported: Number of relations imported
            - errors: List of any errors encountered
            
        Requirements: 13.4
        """
        result = {
            "nodes_imported": 0,
            "relations_imported": 0,
            "errors": []
        }
        
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {str(e)}")
            return result
        
        # Validate structure
        if "nodes" not in data or "relations" not in data:
            result["errors"].append("Invalid format: missing 'nodes' or 'relations' key")
            return result
        
        # Clear existing data if requested
        if clear_existing:
            self.db.query(KnowledgeRelation).delete(synchronize_session=False)
            self.db.query(KnowledgeNode).delete(synchronize_session=False)
            self.db.commit()
        
        # Import nodes
        for node_data in data["nodes"]:
            try:
                # Check if node already exists
                existing = self.get_node(node_data["id"])
                if existing and not clear_existing:
                    continue
                
                node = KnowledgeNode(
                    id=node_data["id"],
                    name=node_data["name"],
                    subject=node_data["subject"],
                    unit=node_data["unit"],
                    difficulty=node_data["difficulty"],
                    description=node_data.get("description")
                )
                self.db.add(node)
                result["nodes_imported"] += 1
            except Exception as e:
                result["errors"].append(f"Error importing node {node_data.get('id', 'unknown')}: {str(e)}")
        
        self.db.commit()
        
        # Import relations
        for relation_data in data["relations"]:
            try:
                # Check if relation already exists
                existing = self.db.query(KnowledgeRelation).filter(
                    KnowledgeRelation.from_id == relation_data["from_id"],
                    KnowledgeRelation.to_id == relation_data["to_id"],
                    KnowledgeRelation.relation_type == relation_data["relation_type"]
                ).first()
                
                if existing and not clear_existing:
                    continue
                
                relation = KnowledgeRelation(
                    from_id=relation_data["from_id"],
                    to_id=relation_data["to_id"],
                    relation_type=relation_data["relation_type"],
                    weight=relation_data.get("weight", 1.0)
                )
                self.db.add(relation)
                result["relations_imported"] += 1
            except Exception as e:
                result["errors"].append(f"Error importing relation: {str(e)}")
        
        self.db.commit()
        
        return result

    def get_all_relations(self) -> List[KnowledgeRelation]:
        """
        Get all relations in the knowledge graph.
        
        Returns:
            List of all KnowledgeRelation objects
        """
        return self.db.query(KnowledgeRelation).all()
